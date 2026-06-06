"""knoq MCP Server - 基于 stdio 的 JSON-RPC MCP 服务器

提供 4 个工具供 AI Agent 调用：
- search_knowledge: 搜索知识
- get_topic: 获取条目详情
- add_knowledge: 添加条目
- export_context: 导出上下文
"""

import json
import sys

from knoq.search import search
from knoq.repository import add_entry, get_entry, list_entries

# 内容长度上限（与 repository.py 一致）
_MAX_CONTENT = 100_000
_MAX_TITLE = 500
_MAX_LIMIT = 100


# MCP 工具定义
TOOLS = [
    {
        "name": "search_knowledge",
        "description": "搜索本地知识库，返回匹配的知识条目",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "limit": {"type": "integer", "description": "最大返回条数", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_topic",
        "description": "按 slug 获取知识条目详情",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "条目 slug"},
            },
            "required": ["slug"],
        },
    },
    {
        "name": "add_knowledge",
        "description": "添加一条知识到本地知识库",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "条目标题"},
                "content": {"type": "string", "description": "Markdown 格式内容"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "标签列表",
                    "default": [],
                },
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "export_context",
        "description": "导出知识上下文，供 Agent 注入 prompt",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询（空则导出全部）", "default": ""},
                "limit": {"type": "integer", "description": "最大条数", "default": 10},
                "budget": {"type": "integer", "description": "最大字符数", "default": 2000},
            },
        },
    },
]


def _require(params: dict, *keys: str) -> None:
    """验证必需参数存在且非空"""
    for key in keys:
        if key not in params or params[key] is None or params[key] == "":
            raise ValueError(f"缺少必需参数: {key}")


def handle_search_knowledge(params: dict) -> str:
    """处理 search_knowledge 调用"""
    _require(params, "query")
    query = str(params["query"]).strip()
    limit = min(int(params.get("limit", 10)), _MAX_LIMIT)
    results = search(query, limit=limit)
    if not results:
        return f"未找到与 '{query}' 相关的知识"
    return "\n\n".join(
        f"### {r.entry.title} (slug: {r.entry.slug})\n{r.snippet}"
        for r in results
    )


def handle_get_topic(params: dict) -> str:
    """处理 get_topic 调用"""
    _require(params, "slug")
    slug = str(params["slug"]).strip()
    entry = get_entry(slug)
    if not entry:
        return f"未找到条目: {slug}"
    return f"# {entry.title}\n\n{entry.content_md}\n\n标签: {', '.join(entry.tags)}"


def handle_add_knowledge(params: dict) -> str:
    """处理 add_knowledge 调用"""
    _require(params, "title", "content")
    title = str(params["title"]).strip()[:_MAX_TITLE]
    content = str(params["content"])[:_MAX_CONTENT]
    tags = params.get("tags", [])
    if not isinstance(tags, list):
        tags = []
    try:
        entry = add_entry(title=title, content_md=content, tags=tags)
        return f"已添加: {entry.slug}"
    except ValueError as e:
        return str(e)


def handle_export_context(params: dict) -> str:
    """处理 export_context 调用"""
    query = str(params.get("query", "")).strip()
    limit = min(int(params.get("limit", 10)), _MAX_LIMIT)
    budget = min(int(params.get("budget", 2000)), 100_000)

    if query:
        results = search(query, limit=limit)
        entries = [r.entry for r in results]
    else:
        entries = list_entries(limit=limit)

    if not entries:
        return "无可导出的知识"

    parts = []
    total_len = 0
    for e in entries:
        part = f"## {e.title}\n\n{e.content_md}"
        if total_len + len(part) > budget:
            break
        parts.append(part)
        total_len += len(part)
    return "\n\n---\n\n".join(parts)


# 工具处理器映射
HANDLERS = {
    "search_knowledge": handle_search_knowledge,
    "get_topic": handle_get_topic,
    "add_knowledge": handle_add_knowledge,
    "export_context": handle_export_context,
}


def make_response(req_id, result):
    """构造 JSON-RPC 成功响应"""
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def make_error(req_id, code, message):
    """构造 JSON-RPC 错误响应"""
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle_request(request: dict) -> dict:
    """处理一个 JSON-RPC 请求"""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return make_response(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "knoq-mcp-server", "version": "0.1.0"},
        })

    if method == "notifications/initialized":
        return None  # 通知不需要响应

    if method == "tools/list":
        return make_response(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments", {})
        handler = HANDLERS.get(tool_name)
        if not handler:
            return make_error(req_id, -32601, f"未知工具: {tool_name}")
        try:
            result_text = handler(tool_args)
            return make_response(req_id, {
                "content": [{"type": "text", "text": result_text}],
            })
        except ValueError as e:
            return make_error(req_id, -32602, str(e))
        except Exception:
            return make_error(req_id, -32000, "内部错误")

    if method == "ping":
        return make_response(req_id, {})

    return make_error(req_id, -32601, f"未知方法: {method}")


def main():
    """MCP stdio 服务器主循环"""
    from knoq.db import init_db
    init_db()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
