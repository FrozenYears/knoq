"""knoq MCP Server - 基于 stdio 的 JSON-RPC MCP 服务器

提供 4 个工具供 AI Agent 调用：
- search_knowledge: 搜索知识
- get_topic: 获取条目详情
- add_knowledge: 添加条目
- export_context: 导出上下文
"""

import json
import sys

from knoq.context import render_entry, render_entries_text
from knoq.search import search
from knoq.repository import (
    MAX_CONTENT_LENGTH,
    MAX_TAG_LENGTH,
    MAX_TAGS,
    MAX_TITLE_LENGTH,
    add_entry,
    get_entry,
    list_entries,
)

_SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
_DEFAULT_PROTOCOL_VERSION = _SUPPORTED_PROTOCOL_VERSIONS[0]
_MAX_LIMIT = 100
_MAX_BUDGET = 100_000
_MAX_QUERY = 500
_MAX_SLUG = 500
_MAX_REQUEST = 1_000_000
_MAX_RESPONSE = 500_000  # MCP 单次响应最大 500KB


# MCP 工具定义


# MCP 工具定义
TOOLS = [
    {
        "name": "search_knowledge",
        "description": "Search the local knoq knowledge base and return matching entries with slug, tags, source, score, and snippet.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query text."},
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": _MAX_LIMIT,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_topic",
        "description": "Get the full content of a knowledge entry by slug.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "slug": {"type": "string", "description": "Entry slug.", "minLength": 1, "maxLength": _MAX_SLUG},
            },
            "required": ["slug"],
            "additionalProperties": False,
        },
    },
    {
        "name": "add_knowledge",
        "description": "Add a new knowledge entry to the local knoq knowledge base.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Entry title.", "minLength": 1, "maxLength": MAX_TITLE_LENGTH},
                "content": {"type": "string", "description": "Entry content in Markdown format.", "maxLength": MAX_CONTENT_LENGTH},
                "tags": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": MAX_TAG_LENGTH},
                    "description": "Optional list of tags.",
                    "default": [],
                    "maxItems": MAX_TAGS,
                },
            },
            "required": ["title", "content"],
            "additionalProperties": False,
        },
    },
    {
        "name": "export_context",
        "description": "Export Agent-ready context from matching knowledge entries within a character budget.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query. Leave empty to export recent entries.", "default": "", "maxLength": _MAX_QUERY},
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of entries to include.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": _MAX_LIMIT,
                },
                "budget": {
                    "type": "integer",
                    "description": "Maximum output size in characters.",
                    "default": 2000,
                    "minimum": 100,
                    "maximum": _MAX_BUDGET,
                },
            },
            "additionalProperties": False,
        },
    },
]


def _require(params: dict, *keys: str) -> None:
    """验证必需参数存在且非空"""
    for key in keys:
        if key not in params or params[key] is None or params[key] == "":
            raise ValueError(f"缺少必需参数: {key}")


def _str_param(params: dict, key: str, max_len: int, required: bool = False) -> str:
    """读取并校验字符串参数。"""
    if required:
        _require(params, key)
    value = str(params.get(key, "")).strip()
    if required and not value:
        raise ValueError(f"缺少必需参数: {key}")
    if len(value) > max_len:
        raise ValueError(f"{key} 过长: {len(value)} 字符（上限 {max_len}）")
    return value


def _int_param(params: dict, key: str, default: int, minimum: int, maximum: int) -> int:
    """读取并校验整数参数。"""
    raw = params.get(key, default)
    if isinstance(raw, bool):
        raise ValueError(f"{key} 必须是整数")
    try:
        value = int(raw)
    except (TypeError, ValueError) as err:
        raise ValueError(f"{key} 必须是整数") from err
    if value < minimum or value > maximum:
        raise ValueError(f"{key} 必须在 {minimum}-{maximum} 之间")
    return value


def _tags_param(params: dict) -> list[str]:
    """读取并校验标签参数。"""
    tags = params.get("tags", [])
    if not isinstance(tags, list):
        raise ValueError("tags 必须是字符串数组")
    normalized = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValueError("tags 必须是字符串数组")
        tag = tag.strip()
        if tag:
            normalized.append(tag)
    if len(normalized) > MAX_TAGS:
        raise ValueError(f"tags 最多 {MAX_TAGS} 个")
    if any(len(tag) > MAX_TAG_LENGTH for tag in normalized):
        raise ValueError(f"单个 tag 最多 {MAX_TAG_LENGTH} 字符")
    return normalized


def handle_search_knowledge(params: dict) -> str:
    """处理 search_knowledge 调用"""
    query = _str_param(params, "query", _MAX_QUERY, required=True)
    limit = _int_param(params, "limit", 10, 1, _MAX_LIMIT)
    results = search(query, limit=limit)
    if not results:
        return f"未找到与 '{query}' 相关的知识"
    return "\n\n".join(
        f"### {r.entry.title}\n- slug: {r.entry.slug}\n- tags: {', '.join(r.entry.tags) or 'none'}\n- source: {r.entry.source_path or 'manual'}\n- score: {r.rank:.4f}\n\n{r.snippet}"
        for r in results
    )


def handle_get_topic(params: dict) -> str:
    """处理 get_topic 调用"""
    slug = _str_param(params, "slug", _MAX_SLUG, required=True)
    entry = get_entry(slug)
    if not entry:
        return f"未找到条目: {slug}"
    return render_entry(entry)


def handle_add_knowledge(params: dict) -> str:
    """处理 add_knowledge 调用"""
    title = _str_param(params, "title", MAX_TITLE_LENGTH, required=True)
    content = _str_param(params, "content", MAX_CONTENT_LENGTH, required=True)
    tags = _tags_param(params)
    try:
        entry = add_entry(title=title, content_md=content, tags=tags)
        return f"已添加: {entry.slug}\n\n{render_entry(entry, include_content=False)}"
    except ValueError as e:
        return str(e)


def handle_export_context(params: dict) -> str:
    """处理 export_context 调用"""
    query = _str_param(params, "query", _MAX_QUERY)
    limit = _int_param(params, "limit", 10, 1, _MAX_LIMIT)
    budget = _int_param(params, "budget", 2000, 100, _MAX_BUDGET)

    if query:
        results = search(query, limit=limit)
        entries = [r.entry for r in results]
    else:
        entries = list_entries(limit=limit)

    if not entries:
        return "无可导出的知识"

    return render_entries_text(entries, budget)


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


def _truncate(text: str, max_len: int = _MAX_RESPONSE) -> str:
    """截断响应文本，防止上下文窗口溢出"""
    if len(text) <= max_len:
        return text
    return text[:max_len] + f"\n\n[已截断：原始长度 {len(text)} 字符，已展示前 {max_len} 字符]"


def handle_request(request: dict) -> dict | None:
    """处理一个 JSON-RPC 请求"""
    if not isinstance(request, dict):
        return make_error(None, -32600, "Invalid Request")

    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return make_error(req_id, -32600, "Invalid params")

    if method == "initialize":
        requested_version = params.get("protocolVersion")
        protocol_version = (
            requested_version
            if requested_version in _SUPPORTED_PROTOCOL_VERSIONS
            else _DEFAULT_PROTOCOL_VERSION
        )
        return make_response(req_id, {
            "protocolVersion": protocol_version,
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
        if not isinstance(tool_name, str):
            return make_error(req_id, -32600, "Tool name must be a string")
        if not isinstance(tool_args, dict):
            return make_error(req_id, -32600, "Tool arguments must be an object")
        handler = HANDLERS.get(tool_name)
        if not handler:
            return make_error(req_id, -32601, f"未知工具: {tool_name}")
        try:
            result_text = _truncate(handler(tool_args))
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
    # Windows 兼容：强制 stdin/stdout 使用 UTF-8
    if sys.platform == "win32":
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    from knoq.db import init_db
    init_db()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if len(line) > _MAX_REQUEST:
            response = make_error(None, -32600, "Request too large")
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            response = make_error(None, -32700, "Parse error")
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        response = handle_request(request)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
