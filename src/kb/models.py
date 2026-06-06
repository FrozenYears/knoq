"""数据模型定义"""

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
