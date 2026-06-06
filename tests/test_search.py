"""search.py 单元测试"""

from kb.repository import add_entry
from kb.search import search, _has_cjk, _make_snippet


class TestHasCjk:
    def test_chinese(self):
        assert _has_cjk("你好") is True

    def test_english(self):
        assert _has_cjk("hello") is False

    def test_mixed(self):
        assert _has_cjk("hello你好") is True

    def test_empty(self):
        assert _has_cjk("") is False


class TestMakeSnippet:
    def test_found(self):
        content = "这是一段很长的文本，其中包含Docker部署相关内容，后面还有很多文字"
        snippet = _make_snippet(content, "Docker")
        assert "Docker" in snippet

    def test_not_found(self):
        content = "没有匹配的内容"
        snippet = _make_snippet(content, "Docker", max_len=10)
        assert len(snippet) <= 10


class TestSearch:
    def test_cjk_search(self):
        add_entry("部署指南", "# 部署\n使用 Docker 部署")
        results = search("部署")
        assert len(results) >= 1
        assert "部署" in results[0].entry.title or "部署" in results[0].snippet

    def test_ascii_fts_search(self):
        add_entry("Docker Guide", "# Docker\nContainer deployment")
        results = search("Docker")
        assert len(results) >= 1

    def test_no_results(self):
        add_entry("无关条目", "内容")
        results = search("xyznonexistent")
        assert len(results) == 0

    def test_limit(self):
        for i in range(5):
            add_entry(f"条目{i}", f"内容{i}")
        results = search("条目", limit=2)
        assert len(results) <= 2
