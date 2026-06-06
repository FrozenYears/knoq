"""FTS 搜索封装"""

import re
import sqlite3
from dataclasses import dataclass

from knoq.db import get_connection
from knoq.models import Entry


@dataclass
class SearchResult:
    """搜索结果"""

    entry: Entry
    rank: float
    snippet: str


def _has_cjk(text: str) -> bool:
    """检测是否包含 CJK 字符"""
    return bool(re.search(r"[一-鿿㐀-䶿]", text))


def _sanitize_fts_query(query: str) -> str:
    """清理 FTS5 查询中的特殊字符"""
    # FTS5 特殊字符：* " ( ) : ^ - + AND OR NOT NEAR
    # 保留字母数字和空格，其余替换为空
    return re.sub(r'[^\w\s]', ' ', query).strip()


def _escape_like(pattern: str) -> str:
    """转义 LIKE 通配符 %、_，使用 / 作为转义符"""
    return pattern.replace("/", "//").replace("%", "/%").replace("_", "/_")


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
            escaped = _escape_like(query)
            like_pattern = f"%{escaped}%"
            rows = conn.execute(
                """
                SELECT * FROM entries
                WHERE title LIKE ? ESCAPE '/' OR content_md LIKE ? ESCAPE '/' OR summary LIKE ? ESCAPE '/'
                ORDER BY updated_at DESC LIMIT ?
                """,
                (like_pattern, like_pattern, like_pattern, limit),
            ).fetchall()
            return [
                SearchResult(entry=Entry.from_row(r), rank=0.0, snippet=_make_snippet(r["content_md"], query))
                for r in rows
            ]
        else:
            fts_query = _sanitize_fts_query(query)
            if not fts_query:
                return []
            rows = conn.execute(
                """
                SELECT e.*, rank,
                       snippet(entries_fts, 1, '>>>', '<<<', '...', 64) AS snip
                FROM entries_fts
                JOIN entries e ON e.id = entries_fts.rowid
                WHERE entries_fts MATCH ?
                ORDER BY rank LIMIT ?
                """,
                (fts_query, limit),
            ).fetchall()
            return [
                SearchResult(entry=Entry.from_row(r), rank=r["rank"], snippet=r["snip"])
                for r in rows
            ]
    finally:
        conn.close()
