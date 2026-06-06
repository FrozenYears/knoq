"""db.py 单元测试"""

from knoq.db import get_connection, init_db, optimize_db, SCHEMA_VERSION, _get_schema_version


class TestInitDb:
    def test_creates_tables(self):
        init_db()
        conn = get_connection()
        try:
            tables = [r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()]
            assert "entries" in tables
        finally:
            conn.close()

    def test_schema_version_set(self):
        init_db()
        conn = get_connection()
        try:
            assert _get_schema_version(conn) == SCHEMA_VERSION
        finally:
            conn.close()


class TestConnection:
    def test_pragmas_set(self):
        conn = get_connection()
        try:
            wal = conn.execute("PRAGMA journal_mode").fetchone()[0]
            assert wal.lower() == "wal"

            busy = conn.execute("PRAGMA busy_timeout").fetchone()[0]
            assert busy == 5000

            sync = conn.execute("PRAGMA synchronous").fetchone()[0]
            assert sync == 1  # NORMAL = 1

            recursive = conn.execute("PRAGMA recursive_triggers").fetchone()[0]
            assert recursive == 1

            temp = conn.execute("PRAGMA temp_store").fetchone()[0]
            assert temp == 2  # MEMORY = 2
        finally:
            conn.close()


class TestOptimize:
    def test_optimize_empty_db(self):
        init_db()
        result = optimize_db()
        assert "entries" in result
        assert result["entries"] == 0
        assert result["size_before"] >= 0
        assert result["size_after"] >= 0

    def test_optimize_with_entries(self):
        from knoq.repository import add_entry
        init_db()
        add_entry("优化测试", "内容" * 100)
        result = optimize_db()
        assert result["entries"] == 1
