"""mcp_server.py 单元测试"""

import json
from knoq.mcp_server import handle_request


def _call(method, params=None, req_id=1):
    """构造并处理一个 JSON-RPC 请求"""
    return handle_request({"jsonrpc": "2.0", "method": method, "params": params or {}, "id": req_id})


class TestInitialize:
    def test_returns_capabilities(self):
        resp = _call("initialize")
        assert resp["result"]["protocolVersion"] == "2024-11-05"
        assert "tools" in resp["result"]["capabilities"]


class TestToolsList:
    def test_has_four_tools(self):
        resp = _call("tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 4
        names = {t["name"] for t in tools}
        assert names == {"search_knowledge", "get_topic", "add_knowledge", "export_context"}


class TestAddKnowledge:
    def test_add(self):
        resp = _call("tools/call", {"name": "add_knowledge", "arguments": {"title": "MCP测试", "content": "内容"}})
        assert "已添加" in resp["result"]["content"][0]["text"]


class TestSearchKnowledge:
    def test_search(self):
        # 先添加
        _call("tools/call", {"name": "add_knowledge", "arguments": {"title": "搜索目标", "content": "hello world"}})
        # 搜索
        resp = _call("tools/call", {"name": "search_knowledge", "arguments": {"query": "hello"}})
        text = resp["result"]["content"][0]["text"]
        assert "搜索目标" in text or "hello" in text


class TestGetTopic:
    def test_found(self):
        # 先添加
        _call("tools/call", {"name": "add_knowledge", "arguments": {"title": "详情测试", "content": "# 详情\n内容"}})
        # 通过 list 获取 slug
        from knoq.repository import list_entries
        slug = list_entries()[0].slug
        resp = _call("tools/call", {"name": "get_topic", "arguments": {"slug": slug}})
        assert "详情" in resp["result"]["content"][0]["text"]

    def test_not_found(self):
        resp = _call("tools/call", {"name": "get_topic", "arguments": {"slug": "不存在"}})
        assert "未找到" in resp["result"]["content"][0]["text"]


class TestExportContext:
    def test_export(self):
        _call("tools/call", {"name": "add_knowledge", "arguments": {"title": "导出测试", "content": "导出内容"}})
        resp = _call("tools/call", {"name": "export_context", "arguments": {"query": "导出"}})
        assert "导出" in resp["result"]["content"][0]["text"]


class TestUnknownMethod:
    def test_returns_error(self):
        resp = _call("unknown/method")
        assert "error" in resp
        assert resp["error"]["code"] == -32601
