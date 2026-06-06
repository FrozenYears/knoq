"""数据模型定义"""

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Entry:
    """知识条目"""

    id: int | None = None
    slug: str = ""
    title: str = ""
    content_md: str = ""
    summary: str = ""
    source_path: str = ""
    hash: str = ""
    tags: list[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    @staticmethod
    def now_iso() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    @staticmethod
    def from_row(row: sqlite3.Row) -> "Entry":
        """从数据库行构造 Entry"""
        return Entry(
            id=row["id"],
            slug=row["slug"],
            title=row["title"],
            content_md=row["content_md"],
            summary=row["summary"],
            source_path=row["source_path"],
            hash=row["hash"],
            tags=json.loads(row["tags"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        """转为字典（用于 JSON 序列化）"""
        return {
            "id": self.id,
            "slug": self.slug,
            "title": self.title,
            "content": self.content_md,
            "summary": self.summary,
            "tags": self.tags,
            "source_path": self.source_path,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
