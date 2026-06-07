"""Agent 上下文导出工具。"""

import json

from knoq.models import Entry


def render_entry(entry: Entry, include_content: bool = True) -> str:
    """渲染单条知识为 Agent 易读文本。"""
    tags = ", ".join(entry.tags) if entry.tags else "none"
    source = entry.source_path or "manual"
    parts = [
        f"## {entry.title}",
        f"- slug: {entry.slug}",
        f"- tags: {tags}",
        f"- source: {source}",
    ]
    if entry.summary:
        parts.append(f"- summary: {entry.summary}")
    if include_content:
        parts.append("")
        parts.append(entry.content_md)
    return "\n".join(parts)


def render_entries_text(entries: list[Entry], budget: int) -> str:
    """按预算导出多条知识文本。"""
    parts = []
    total_len = 0
    for entry in entries:
        part = render_entry(entry)
        if total_len + len(part) > budget:
            break
        parts.append(part)
        total_len += len(part)
    return "\n\n---\n\n".join(parts)


def render_entries_json(entries: list[Entry], budget: int) -> str:
    """按预算导出多条知识 JSON。"""
    items = []
    total_len = 0
    for entry in entries:
        item = {
            "slug": entry.slug,
            "title": entry.title,
            "summary": entry.summary,
            "content": entry.content_md,
            "tags": entry.tags,
            "source_path": entry.source_path,
            "updated_at": entry.updated_at,
        }
        item_len = len(json.dumps(item, ensure_ascii=False))
        if total_len + item_len > budget:
            break
        items.append(item)
        total_len += item_len
    return json.dumps(items, ensure_ascii=False, indent=2)
