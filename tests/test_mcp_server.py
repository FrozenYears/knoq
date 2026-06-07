"""mcp_server.py 单元测试"""

import json
import os
import subprocess
import sys
from knoq.mcp_server import handle_request


def _call(method, params=None, req_id=1):
    """构造并处理一个 JSON-RPC 请求"""
    return handle_request({"jsonrpc": "2.0", "method": method, "params": params or {}, "id": req_id})


class TestInitialize:
    def test_returns_capabilities(self):
        resp = _call("initialize")
        assert resp["result"]["protocolVersion"] == "2025-11-25"
        assert "tools" in resp["result"]["capabilities"]

    def test_uses_supported_client_protocol_version(self):
        resp = _call("initialize", {"protocolVersion": "2024-11-05"})
        assert resp["result"]["protocolVersion"] == "2024-11-05"


class TestToolsList:
    def test_has_four_tools(self):
        resp = _call("tools/list")
        tools = resp["result"]["tools"]
        assert len(tools) == 4
        names = {t["name"] for t in tools}
        assert names == {"search_knowledge", "get_topic", "add_knowledge", "export_context"}
        for tool in tools:
            assert tool["inputSchema"].get("additionalProperties") is False


class TestAddKnowledge:
    def test_add(self):
        resp = _call("tools/call", {"name": "add_knowledge", "arguments": {"title": "MCP测试", "content": "内容"}})
        assert "已添加" in resp["result"]["content"][0]["text"]
        assert "slug:" in resp["result"]["content"][0]["text"]

    def test_rejects_invalid_tags(self):
        resp = _call("tools/call", {"name": "add_knowledge", "arguments": {"title": "x", "content": "y", "tags": "bad"}})
        assert "error" in resp
        assert resp["error"]["code"] == -32602


class TestSearchKnowledge:
    def test_search(self):
        # 先添加
        _call("tools/call", {"name": "add_knowledge", "arguments": {"title": "搜索目标", "content": "hello world"}})
        # 搜索
        resp = _call("tools/call", {"name": "search_knowledge", "arguments": {"query": "hello"}})
        text = resp["result"]["content"][0]["text"]
        assert "搜索目标" in text or "hello" in text
        assert "slug:" in text

    def test_rejects_bad_limit(self):
        resp = _call("tools/call", {"name": "search_knowledge", "arguments": {"query": "hello", "limit": 0}})
        assert "error" in resp
        assert resp["error"]["code"] == -32602


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
        text = resp["result"]["content"][0]["text"]
        assert "导出" in text
        assert "slug:" in text


class TestUnknownMethod:
    def test_returns_error(self):
        resp = _call("unknown/method")
        assert "error" in resp
        assert resp["error"]["code"] == -32601


class TestInvalidRequests:
    def test_non_object_request_returns_error(self):
        resp = handle_request([])
        assert resp["error"]["code"] == -32600

    def test_non_object_params_returns_error(self):
        resp = handle_request({"jsonrpc": "2.0", "method": "tools/call", "params": [], "id": 1})
        assert resp["error"]["code"] == -32600

    def test_non_object_tool_arguments_returns_error(self):
        resp = _call("tools/call", {"name": "search_knowledge", "arguments": []})
        assert resp["error"]["code"] == -32600


class TestMcpStdio:
    def test_stdio_agent_flow(self, tmp_path):
        env = {**os.environ, "KNOQ_HOME": str(tmp_path / ".knoq")}
        requests = [
            {"jsonrpc": "2.0", "method": "initialize", "params": {"protocolVersion": "2025-11-25"}, "id": 1},
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "add_knowledge",
                    "arguments": {"title": "Agent Tool Guide", "content": "Use search_knowledge.", "tags": ["agent"]},
                },
                "id": 2,
            },
            {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {"name": "search_knowledge", "arguments": {"query": "Agent", "limit": 3}},
                "id": 3,
            },
        ]
        payload = "\n".join(json.dumps(req) for req in requests) + "\n"

        proc = subprocess.run(
            [sys.executable, "-m", "knoq.mcp_server"],
            input=payload,
            text=True,
            capture_output=True,
            env=env,
            timeout=10,
            check=True,
            encoding="utf-8",
        )
        responses = [json.loads(line) for line in proc.stdout.splitlines()]
        assert responses[0]["result"]["protocolVersion"] == "2025-11-25"
        assert "slug:" in responses[1]["result"]["content"][0]["text"]
        assert "tags:" in responses[2]["result"]["content"][0]["text"]
