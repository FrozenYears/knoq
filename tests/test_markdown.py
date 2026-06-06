"""markdown.py 单元测试"""

from kb.markdown import extract_title, extract_tags, extract_summary


class TestExtractTitle:
    def test_h1(self):
        assert extract_title("# Hello World") == "Hello World"

    def test_no_title(self):
        assert extract_title("no title here", fallback="default") == "default"

    def test_multiline(self):
        content = "line1\n# Title\nmore"
        assert extract_title(content) == "Title"


class TestExtractTags:
    def test_ascii_tags(self):
        tags = extract_tags("#deploy #docker")
        assert "deploy" in tags
        assert "docker" in tags

    def test_cjk_tags(self):
        tags = extract_tags("#部署 #测试")
        assert "部署" in tags

    def test_no_tags(self):
        assert extract_tags("no tags here") == []


class TestExtractSummary:
    def test_basic(self):
        content = "# Title\nFirst paragraph here"
        assert extract_summary(content) == "First paragraph here"

    def test_title_only(self):
        assert extract_summary("# Only Title") == ""

    def test_max_len(self):
        content = "# T\n" + "a" * 300
        summary = extract_summary(content, max_len=50)
        assert len(summary) <= 50
