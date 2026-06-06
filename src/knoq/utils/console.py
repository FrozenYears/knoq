"""CLI 输出格式化"""

import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

# Windows 兼容：强制 UTF-8 输出
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

console = Console()


def success(msg: str) -> None:
    console.print(f"[green][OK][/green] {msg}")


def error(msg: str) -> None:
    console.print(f"[red][ERR][/red] {msg}")


def info(msg: str) -> None:
    console.print(f"[blue][INFO][/blue] {msg}")


def print_entry_table(entries) -> None:
    """以表格形式展示条目列表"""
    table = Table(title="知识条目", show_lines=False)
    table.add_column("Slug", style="cyan", max_width=24)
    table.add_column("标题", style="bold")
    table.add_column("摘要", max_width=48)
    table.add_column("标签", style="dim")
    table.add_column("更新时间", style="dim")

    for e in entries:
        tags_str = ", ".join(e.tags) if e.tags else ""
        table.add_row(e.slug, e.title, e.summary[:48], tags_str, e.updated_at[:10])

    console.print(table)


def print_entry_detail(entry) -> None:
    """展示条目详情"""
    panel = Panel(
        Markdown(entry.content_md),
        title=f"[bold cyan]{entry.title}[/bold cyan]",
        subtitle=f"slug: {entry.slug} | 更新: {entry.updated_at[:10]}",
        border_style="blue",
    )
    console.print(panel)
