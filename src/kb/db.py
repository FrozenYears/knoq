"""SQLite 连接、初始化、迁移"""

import sqlite3
from pathlib import Path

from kb.paths import db_path, ensure_home

# 建表 SQL
SCHEMA_SQL = """\
-- 知识条目主表
CREATE TABLE IF NOT EXISTS entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    content_md TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    source_path TEXT NOT NULL UNIQUE,
    hash TEXT NOT NULL,
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_entries_updated_at ON entries(updated_at);
CREATE INDEX IF NOT EXISTS idx_entries_title ON entries(title);

-- FTS5 全文搜索虚拟表
CREATE VIRTUAL TABLE IF NOT EXISTS entries_fts USING fts5(
    title,
    content_md,
    summary,
    content='entries',
    content_rowid='id',
    tokenize='unicode61'
);
"""


def get_connection() -> sqlite3.Connection:
    """获取数据库连接"""
    ensure_home()
    conn = sqlite3.connect(str(db_path()))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """初始化数据库表结构"""
    conn = get_connection()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()
