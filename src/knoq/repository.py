"""知识条目的增删改查"""

import hashlib
import json
import re
import sqlite3

from knoq.db import get_connection
from knoq.models import Entry

# 内容长度上限
MAX_CONTENT_LENGTH = 100_000  # 100KB
MAX_TITLE_LENGTH = 500
MAX_TAGS = 20
MAX_TAG_LENGTH = 64
MAX_SOURCE_PATH_LENGTH = 1_000


def make_slug(title: str) -> str:
    """从标题生成 slug

    - ASCII 标题：转小写，空格转连字符
    - CJK 标题：保留原始字符 + 短 hash 保证唯一性
    """
    slug = title.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")

    if not slug:
        return "untitled"

    # CJK 字符保留可读性，追加短 hash 防冲突
    if any(ord(c) > 127 for c in slug):
        h = hashlib.md5(title.encode()).hexdigest()[:6]
        return f"{slug}-{h}"

    return slug


def content_hash(content: str) -> str:
    """计算内容哈希"""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def validate_entry_input(title: str | None = None, tags: list[str] | None = None, source_path: str = "") -> list[str] | None:
    """校验并规范化条目输入。"""
    if title is not None:
        title = title.strip()
        if not title:
            raise ValueError("标题不能为空")
        if len(title) > MAX_TITLE_LENGTH:
            raise ValueError(f"标题过长: {len(title)} 字符（上限 {MAX_TITLE_LENGTH}）")

    if len(source_path) > MAX_SOURCE_PATH_LENGTH:
        raise ValueError(f"来源路径过长: {len(source_path)} 字符（上限 {MAX_SOURCE_PATH_LENGTH}）")

    if tags is None:
        return None

    normalized = []
    for tag in tags:
        if not isinstance(tag, str):
            raise ValueError("标签必须是字符串")
        tag = tag.strip()
        if not tag:
            continue
        if len(tag) > MAX_TAG_LENGTH:
            raise ValueError(f"标签过长: {tag[:20]}...（上限 {MAX_TAG_LENGTH}）")
        normalized.append(tag)

    if len(normalized) > MAX_TAGS:
        raise ValueError(f"标签过多: {len(normalized)} 个（上限 {MAX_TAGS}）")

    return normalized


def add_entry(title: str, content_md: str, tags: list[str] | None = None, source_path: str = "") -> Entry:
    """添加知识条目"""
    if len(content_md) > MAX_CONTENT_LENGTH:
        raise ValueError(f"内容过长: {len(content_md)} 字符（上限 {MAX_CONTENT_LENGTH}）")
    tags = validate_entry_input(title=title, tags=tags or [], source_path=source_path)
    title = title.strip()

    slug = make_slug(title)
    summary = content_md[:200].split("\n")[0] if content_md else ""
    h = content_hash(content_md)
    now = Entry.now_iso()

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
    except sqlite3.Error as e:
        raise ValueError(f"数据库错误: {e}") from e
    finally:
        conn.close()


def update_entry(slug: str, title: str | None = None, content_md: str | None = None,
                 tags: list[str] | None = None) -> Entry | None:
    """更新已有条目"""
    if content_md is not None and len(content_md) > MAX_CONTENT_LENGTH:
        raise ValueError(f"内容过长: {len(content_md)} 字符（上限 {MAX_CONTENT_LENGTH}）")
    tags = validate_entry_input(title=title, tags=tags)
    if title is not None:
        title = title.strip()

    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM entries WHERE slug = ?", (slug,)).fetchone()
        if not row:
            return None

        new_title = title or row["title"]
        new_content = content_md if content_md is not None else row["content_md"]
        new_summary = new_content[:200].split("\n")[0] if new_content else ""
        new_hash = content_hash(new_content)
        new_tags = json.dumps(tags, ensure_ascii=False) if tags is not None else row["tags"]
        return_tags = tags if tags is not None else json.loads(row["tags"])
        now = Entry.now_iso()

        conn.execute(
            """UPDATE entries SET title=?, content_md=?, summary=?, hash=?, tags=?, updated_at=?
            WHERE slug=?""",
            (new_title, new_content, new_summary, new_hash, new_tags, now, slug),
        )
        conn.commit()

        return Entry(
            id=row["id"], slug=slug, title=new_title, content_md=new_content,
            summary=new_summary, source_path=row["source_path"], hash=new_hash,
            tags=return_tags, created_at=row["created_at"], updated_at=now,
        )
    except sqlite3.Error as e:
        raise ValueError(f"数据库错误: {e}") from e
    finally:
        conn.close()


def get_entry(slug: str) -> Entry | None:
    """按 slug 获取条目"""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM entries WHERE slug = ?", (slug,)).fetchone()
        return Entry.from_row(row) if row else None
    finally:
        conn.close()


def list_entries(limit: int = 50, offset: int = 0) -> list[Entry]:
    """列出条目"""
    limit = max(0, limit)
    offset = max(0, offset)

    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM entries ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [Entry.from_row(r) for r in rows]
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
    except sqlite3.Error as e:
        raise ValueError(f"数据库错误: {e}") from e
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
