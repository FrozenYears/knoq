"""知识条目的增删改查"""

import hashlib
import json
import re
import sqlite3
from pathlib import Path

from kb.db import get_connection
from kb.models import Entry
from kb.search import _row_to_entry


def make_slug(title: str) -> str:
    """从标题生成 slug"""
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug or "untitled"


def content_hash(content: str) -> str:
    """计算内容哈希"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def add_entry(title: str, content_md: str, tags: list[str] | None = None, source_path: str = "") -> Entry:
    """添加知识条目"""
    slug = make_slug(title)
    summary = content_md[:200].split("\n")[0] if content_md else ""
    h = content_hash(content_md)
    now = Entry.now_iso()
    tags = tags or []

    conn = get_connection()
    try:
        cursor = conn.execute(
            """
            INSERT INTO entries (slug, title, content_md, summary, source_path, hash, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (slug, title, content_md, summary, source_path, h, json.dumps(tags, ensure_ascii=False), now, now),
        )
        rowid = cursor.lastrowid
        conn.commit()

        return Entry(
            id=rowid, slug=slug, title=title, content_md=content_md,
            summary=summary, source_path=source_path, hash=h,
            tags=tags, created_at=now, updated_at=now,
        )
    except sqlite3.IntegrityError:
        raise ValueError(f"条目 '{slug}' 已存在")
    finally:
        conn.close()


def get_entry(slug: str) -> Entry | None:
    """按 slug 获取条目"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM entries WHERE slug = ?", (slug,)).fetchone()
        return _row_to_entry(row) if row else None
    finally:
        conn.close()


def list_entries(limit: int = 50, offset: int = 0) -> list[Entry]:
    """列出条目"""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM entries ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [_row_to_entry(r) for r in rows]
    finally:
        conn.close()


def remove_entry(slug: str) -> bool:
    """删除条目"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM entries WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM entries WHERE id = ?", (row["id"],))
        conn.commit()
        return True
    finally:
        conn.close()


def count_entries() -> int:
    """统计条目数量"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT COUNT(*) as cnt FROM entries").fetchone()
        return row["cnt"]
    finally:
        conn.close()
