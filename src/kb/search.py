"""FTS 搜索封装"""

import re
import sqlite3
from dataclasses import dataclass

from kb.db import get_connection
from kb.models import Entry


@dataclass
class SearchResult:
    """搜索结果"""

    entry: Entry
    rank: float
    snippet: str


def _has_cjk(text: str) -> bool:
    """检测是否包含 CJK 字符"""
    return bool(re.search(r"[一-鿿㐀-䶿]", text))


def _make_snippet(content: str, query: str, max_len: int = 120) -> str:
    """从内容中提取包含查询词的摘要片段"""
    idx = content.lower().find(query.lower())
    if idx == -1:
        return content[:max_len]
    start = max(0, idx - 40)
    end = min(len(content), idx + len(query) + 80)
    snippet = content[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(content):
        snippet = snippet + "..."
    return snippet


def search(query: str, limit: int = 20) -> list[SearchResult]:
    """全文搜索知识条目（自动处理 CJK 文本）"""
    conn = get_connection()
    try:
        if _has_cjk(query):
            like_pattern = f"%{query}%"
            rows = conn.execute(
                """
                SELECT * FROM entries
                WHERE title LIKE ? OR content_md LIKE ? OR summary LIKE ?
                ORDER BY updated_at DESC LIMIT ?
                """,
                (like_pattern, like_pattern, like_pattern, limit),
            ).fetchall()
            return [
                SearchResult(entry=Entry.from_row(r), rank=0.0, snippet=_make_snippet(r["content_md"], query))
                for r in rows
            ]
        else:
            rows = conn.execute(
                """
                SELECT e.*, rank,
                       snippet(entries_fts, 1, '>>>', '<<<', '...', 64) AS snip
                FROM entries_fts
                JOIN entries e ON e.id = entries_fts.rowid
                WHERE entries_fts MATCH ?
                ORDER BY rank LIMIT ?
                """,
                (query, limit),
            ).fetchall()
            return [
                SearchResult(entry=Entry.from_row(r), rank=r["rank"], snippet=r["snip"])
                for r in rows
            ]
    finally:
        conn.close()
