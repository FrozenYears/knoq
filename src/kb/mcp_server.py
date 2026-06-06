"""kb MCP Server - 基于 stdio 的 JSON-RPC MCP 服务器

提供 4 个工具供 AI Agent 调用：
- search_knowledge: 搜索知识
- get_topic: 获取条目详情
- add_knowledge: 添加条目
- export_context: 导出上下文
"""

import json
import sys

# 初始化数据库（确保表存在）
from kb.db import init_db
init_db()

from kb.search import search
from kb.repository import add_entry, get_entry, list_entries
from kb.models import Entry

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


def handle_search_knowledge(params: dict) -> str:
    """处理 search_knowledge 调用"""
    query = params["query"]
    limit = params.get("limit", 10)
    results = search(query, limit=limit)
    if not results:
        return f"未找到与 '{query}' 相关的知识"
    parts = []
    for r in results:
        parts.append(f"### {r.entry.title} (slug: {r.entry.slug})\n{r.snippet}")
    return "\n\n".join(parts)


def handle_get_topic(params: dict) -> str:
    """处理 get_topic 调用"""
    slug = params["slug"]
    entry = get_entry(slug)
    if not entry:
        return f"未找到条目: {slug}"
    return f"# {entry.title}\n\n{entry.content_md}\n\n标签: {', '.join(entry.tags)}"


def handle_add_knowledge(params: dict) -> str:
    """处理 add_knowledge 调用"""
    title = params["title"]
    content = params["content"]
    tags = params.get("tags", [])
    try:
        entry = add_entry(title=title, content_md=content, tags=tags)
        return f"已添加: {entry.slug}"
    except ValueError as e:
        return str(e)


def handle_export_context(params: dict) -> str:
    """处理 export_context 调用"""
    query = params.get("query", "")
    limit = params.get("limit", 10)
    budget = params.get("budget", 2000)

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
            "serverInfo": {"name": "kb-mcp-server", "version": "0.1.0"},
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
        except Exception as e:
            return make_error(req_id, -32000, str(e))

    if method == "ping":
        return make_response(req_id, {})

    return make_error(req_id, -32601, f"未知方法: {method}")


def main():
    """MCP stdio 服务器主循环"""
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
