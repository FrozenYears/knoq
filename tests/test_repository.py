"""repository.py 单元测试"""

from knoq.repository import add_entry, get_entry, list_entries, remove_entry, update_entry, count_entries, make_slug


class TestMakeSlug:
    def test_ascii(self):
        assert make_slug("Hello World") == "hello-world"

    def test_cjk(self):
        slug = make_slug("部署流程")
        assert slug  # CJK slug 非空

    def test_empty(self):
        assert make_slug("") == "untitled"


class TestAddEntry:
    def test_basic(self):
        entry = add_entry("测试", "# 测试\n内容")
        assert entry.title == "测试"
        assert entry.id is not None
        assert entry.slug

    def test_empty_title_raises(self):
        try:
            add_entry("  ", "内容")
            assert False, "应抛出 ValueError"
        except ValueError:
            pass

    def test_with_tags(self):
        entry = add_entry("标签测试", "内容", tags=["a", "b"])
        assert entry.tags == ["a", "b"]

    def test_too_many_tags_raises(self):
        try:
            add_entry("标签过多", "内容", tags=[f"t{i}" for i in range(21)])
            assert False, "应抛出 ValueError"
        except ValueError:
            pass

    def test_non_string_tag_raises(self):
        try:
            add_entry("非法标签", "内容", tags=["ok", 1])
            assert False, "应抛出 ValueError"
        except ValueError:
            pass

    def test_duplicate_raises(self):
        add_entry("重复", "内容")
        try:
            add_entry("重复", "内容2")
            assert False, "应抛出 ValueError"
        except ValueError:
            pass


class TestGetEntry:
    def test_found(self):
        add_entry("查找", "内容")
        entries = list_entries()
        slug = entries[0].slug
        entry = get_entry(slug)
        assert entry is not None
        assert entry.title == "查找"

    def test_not_found(self):
        assert get_entry("不存在") is None


class TestUpdateEntry:
    def test_update_content(self):
        add_entry("更新测试", "原始内容")
        entries = list_entries()
        slug = entries[0].slug
        entry = update_entry(slug, content_md="新内容")
        assert entry is not None
        assert entry.content_md == "新内容"

    def test_clear_tags_returns_empty_list(self):
        entry = add_entry("标签清空", "内容", tags=["old"])
        updated = update_entry(entry.slug, tags=[])
        assert updated is not None
        assert updated.tags == []
        assert get_entry(entry.slug).tags == []

    def test_update_not_found(self):
        assert update_entry("不存在", title="x") is None

    def test_update_empty_title_raises(self):
        entry = add_entry("原标题", "内容")
        try:
            update_entry(entry.slug, title="  ")
            assert False, "应抛出 ValueError"
        except ValueError:
            pass


class TestRemoveEntry:
    def test_remove(self):
        add_entry("删除测试", "内容")
        entries = list_entries()
        slug = entries[0].slug
        assert remove_entry(slug) is True
        assert get_entry(slug) is None

    def test_remove_not_found(self):
        assert remove_entry("不存在") is False


class TestListEntries:
    def test_empty(self):
        assert list_entries() == []

    def test_multiple(self):
        add_entry("A", "a")
        add_entry("B", "b")
        assert count_entries() == 2
        entries = list_entries()
        assert len(entries) == 2

    def test_negative_limit_returns_empty(self):
        add_entry("A", "a")
        assert list_entries(limit=-1) == []


class TestCountEntries:
    def test_zero(self):
        assert count_entries() == 0

    def test_after_add(self):
        add_entry("计数", "内容")
        assert count_entries() == 1
