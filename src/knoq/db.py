"""SQLite 连接、初始化、迁移

参考 simonw/sqlite-utils、rtk-ai/rtk 的最佳实践：
- WAL + busy_timeout + synchronous=NORMAL 保证并发安全
- recursive_triggers=ON 保证 FTS 触发器在 REPLACE/级联时正确触发
- temp_store=MEMORY 避免 VACUUM 时 /tmp 空间不足
- FTS5 detail=none + columnsize=0 减小索引体积（可节省 80%+）
- PRAGMA user_version 实现 schema 版本迁移
"""

import sqlite3

from knoq.paths import db_path, ensure_home

# 当前 schema 版本号（递增修改）
SCHEMA_VERSION = 1

# 建表 SQL
SCHEMA_SQL = """\
-- 知识条目主表
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content_md TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    source_path TEXT NOT NULL DEFAULT '',
    hash TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entries_updated_at ON entries(updated_at);
CREATE INDEX IF NOT EXISTS idx_entries_title ON entries(title);
CREATE INDEX IF NOT EXISTS idx_entries_source_path ON entries(source_path);

-- FTS5 全文搜索虚拟表（external content 模式）
-- detail=full: 完整存储，支持所有查询类型（短语、前缀等）
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    title,
    content_md,
    summary,
    content='entries',
    content_rowid='id',
    tokenize='unicode61'
);

-- FTS 自动同步触发器
CREATE TRIGGER IF NOT EXISTS entries_ai AFTER INSERT ON entries BEGIN
    INSERT INTO entries_fts(rowid, title, content_md, summary)
    VALUES (new.id, new.title, new.content_md, new.summary);
END;

CREATE TRIGGER IF NOT EXISTS entries_ad AFTER DELETE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, content_md, summary)
    VALUES ('delete', old.id, old.title, old.content_md, old.summary);
END;

CREATE TRIGGER IF NOT EXISTS entries_au AFTER UPDATE ON entries BEGIN
    INSERT INTO entries_fts(entries_fts, rowid, title, content_md, summary)
    VALUES ('delete', old.id, old.title, old.content_md, old.summary);
    INSERT INTO entries_fts(rowid, title, content_md, summary)
    VALUES (new.id, new.title, new.content_md, new.summary);
END;
"""

# 迁移脚本：版本号 -> SQL 列表
MIGRATIONS = {
    # v1 -> v2 示例:
    # 2: ["ALTER TABLE entries ADD COLUMN priority INTEGER DEFAULT 0"],
}


def get_connection() -> sqlite3.Connection:
    """获取数据库连接，设置所有必要的 PRAGMA"""
    ensure_home()
    conn = sqlite3.connect(str(db_path()), timeout=10)
    conn.row_factory = sqlite3.Row
    # 并发安全
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA synchronous=NORMAL")
    # 触发器：确保 REPLACE 和级联 DELETE 时触发器正确执行
    conn.execute("PRAGMA recursive_triggers=ON")
    # 临时数据存内存，避免 VACUUM 时 /tmp 空间不足
    conn.execute("PRAGMA temp_store=MEMORY")
    # 外键约束
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _get_schema_version(conn: sqlite3.Connection) -> int:
    """获取当前 schema 版本"""
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    """设置 schema 版本"""
    conn.execute(f"PRAGMA user_version={version}")


def _run_migrations(conn: sqlite3.Connection) -> None:
    """执行 schema 迁移"""
    current = _get_schema_version(conn)
    target = SCHEMA_VERSION
    if current >= target:
        return
    for version in range(current + 1, target + 1):
        if version in MIGRATIONS:
            for sql in MIGRATIONS[version]:
                conn.execute(sql)
    _set_schema_version(conn, target)
    conn.commit()


def init_db() -> None:
    """初始化数据库表结构并执行迁移"""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        _run_migrations(conn)
        conn.commit()
    finally:
        conn.close()


def optimize_db() -> dict:
    """优化数据库：重建 FTS 索引 + WAL checkpoint + 分析

    返回优化结果统计。
    """
    conn = get_connection()
    try:
        # 获取优化前的大小
        page_count = conn.execute("PRAGMA page_count").fetchone()[0]
        page_size = conn.execute("PRAGMA page_size").fetchone()[0]
        size_before = page_count * page_size

        # 1. 重建 FTS 索引（清理膨胀的 _fts_docsize 等影子表）
        conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")

        # 2. 合并 FTS5 b-tree（优化查询性能）
        conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('optimize')")

        # 3. 先 commit 释放写锁，再做 WAL checkpoint
        conn.commit()

        # 4. WAL checkpoint（将 WAL 日志合并回主数据库）
        # PASSIVE 模式：不阻塞读者，跳过有活跃读事务的页面
        conn.execute("PRAGMA wal_checkpoint(PASSIVE)")

        # 5. 更新统计信息
        conn.execute("ANALYZE")

        conn.commit()

        # 获取优化后的大小
        page_count = conn.execute("PRAGMA page_count").fetchone()[0]
        size_after = page_count * page_size

        entry_count = conn.execute("SELECT COUNT(*) FROM entries").fetchone()[0]

        return {
            "entries": entry_count,
            "size_before": size_before,
            "size_after": size_after,
            "saved": size_before - size_after,
        }
    finally:
        conn.close()
