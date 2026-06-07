"""Typer CLI 主入口"""

import os
from pathlib import Path

import typer

from knoq import __version__

app = typer.Typer(
    name="knoq",
    help="面向仓库的本地 CLI 知识账本",
    no_args_is_help=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"knoq {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="显示版本号",
        callback=_version_callback, is_eager=True,
    ),
) -> None:
    """knoq — 面向仓库的本地 CLI 知识账本"""


@app.command()
def init():
    """初始化知识库（在当前目录创建 .knoq/）"""
    from knoq.db import init_db
    from knoq.utils.console import success, info

    knoq_dir = Path.cwd() / ".knoq"
    os.environ["KNOQ_HOME"] = str(knoq_dir)
    init_db()
    success("知识库已初始化")
    info(f"数据目录: {knoq_dir}")
    info("使用 'knoq add' 添加知识条目")


@app.command()
def optimize():
    """优化数据库：重建 FTS 索引、WAL checkpoint、更新统计"""
    from knoq.db import optimize_db
    from knoq.utils.console import success, info

    def _fmt(size: int) -> str:
        if size < 1024:
            return f"{size}B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f}KB"
        else:
            return f"{size / (1024 * 1024):.1f}MB"

    result = optimize_db()
    success("数据库已优化")
    info(f"条目数: {result['entries']}")
    info(f"优化前: {_fmt(result['size_before'])} -> 优化后: {_fmt(result['size_after'])}")
    if result["saved"] > 0:
        info(f"节省: {_fmt(result['saved'])}")


@app.command()
def add(
    title: str = typer.Argument(..., help="条目标题"),
    content: str = typer.Option("", "--content", "-c", help="Markdown 内容"),
    tags: str = typer.Option("", "--tags", "-t", help="标签，逗号分隔"),
    source: str = typer.Option("", "--source", "-s", help="来源文件路径"),
):
    """添加一条知识条目"""
    import sys
    from knoq.repository import add_entry
    from knoq.markdown import extract_tags
    from knoq.utils.console import success, error

    if not content:
        if sys.stdin.isatty():
            error("请通过 -c 提供内容，或通过管道传入")
            raise typer.Exit(1)
        content = sys.stdin.read().strip()

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else extract_tags(content)

    try:
        entry = add_entry(title=title, content_md=content, tags=tag_list, source_path=source)
        success(f"已添加: {entry.slug}")
    except ValueError as e:
        error(str(e))
        raise typer.Exit(1)


@app.command()
def search(
    query: str = typer.Argument(..., help="搜索关键词"),
    limit: int = typer.Option(20, "--limit", "-n", min=1, max=100, help="返回条数"),
):
    """搜索知识"""
    from knoq.search import search as do_search
    from knoq.utils.console import console, error

    results = do_search(query, limit=limit)
    if not results:
        error("未找到匹配结果")
        raise typer.Exit(0)

    for i, r in enumerate(results, 1):
        console.print(f"[cyan]{i}.[/cyan] [bold]{r.entry.title}[/bold]  (slug: {r.entry.slug})")
        console.print(f"   {r.snippet}")
        console.print()


@app.command()
def show(
    slug: str = typer.Argument(..., help="条目 slug"),
):
    """查看条目详情"""
    from knoq.repository import get_entry
    from knoq.utils.console import print_entry_detail, error

    entry = get_entry(slug)
    if not entry:
        error(f"未找到条目: {slug}")
        raise typer.Exit(1)
    print_entry_detail(entry)


@app.command("list")
def list_cmd(
    limit: int = typer.Option(50, "--limit", "-n", min=1, max=500, help="返回条数"),
    offset: int = typer.Option(0, "--offset", min=0, help="偏移量"),
):
    """列出知识条目"""
    from knoq.repository import list_entries, count_entries
    from knoq.utils.console import print_entry_table, info

    entries = list_entries(limit=limit, offset=offset)
    total = count_entries()
    if not entries:
        info("知识库为空，使用 'knoq add' 添加条目")
        return
    print_entry_table(entries)
    info(f"共 {total} 条，显示 {offset + 1}-{offset + len(entries)}")


@app.command()
def update(
    slug: str = typer.Argument(..., help="条目 slug"),
    title: str = typer.Option(None, "--title", help="新标题"),
    content: str = typer.Option(None, "--content", "-c", help="新内容"),
    tags: str = typer.Option(None, "--tags", "-t", help="新标签，逗号分隔"),
):
    """更新已有条目"""
    from knoq.repository import update_entry
    from knoq.utils.console import success, error

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    entry = update_entry(slug, title=title, content_md=content, tags=tag_list)
    if entry:
        success(f"已更新: {entry.slug}")
    else:
        error(f"未找到条目: {slug}")
        raise typer.Exit(1)


@app.command()
def remove(
    slug: str = typer.Argument(..., help="条目 slug"),
    force: bool = typer.Option(False, "--force", "-f", help="跳过确认"),
):
    """删除知识条目"""
    from knoq.repository import remove_entry
    from knoq.utils.console import success, error

    if not force:
        confirm = typer.confirm(f"确认删除 '{slug}'?")
        if not confirm:
            raise typer.Abort()

    if remove_entry(slug):
        success(f"已删除: {slug}")
    else:
        error(f"未找到条目: {slug}")
        raise typer.Exit(1)


@app.command()
def scan(
    path: str = typer.Option(".", "--path", "-p", help="项目根目录"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅预览，不入库"),
):
    """扫描项目自动提取知识"""
    from pathlib import Path
    from knoq.markdown import scan_project_files
    from knoq.repository import add_entry
    from knoq.utils.console import success, info, error

    root = Path(path).resolve()
    if not root.is_dir():
        error(f"目录不存在: {root}")
        raise typer.Exit(1)

    candidates = scan_project_files(root)
    if not candidates:
        info("未发现可提取的项目文件")
        return

    for item in candidates:
        if dry_run:
            info(f"[预览] {item['title']} <- {item['source']}")
        else:
            try:
                entry = add_entry(
                    title=item["title"],
                    content_md=item["content"],
                    tags=item["tags"],
                    source_path=item["source"],
                )
                success(f"已添加: {entry.slug}")
            except ValueError:
                info(f"已存在，跳过: {item['title']}")

    if dry_run:
        info(f"共发现 {len(candidates)} 个文件，使用 --dry-run 预览模式未入库")


@app.command()
def export(
    query: str = typer.Argument("", help="搜索查询（空则导出全部）"),
    limit: int = typer.Option(10, "--limit", "-n", min=1, max=100, help="最大条数"),
    budget: int = typer.Option(2000, "--budget", "-b", min=100, max=100_000, help="最大字符数"),
    format: str = typer.Option("text", "--format", "-f", help="输出格式: text/json"),
):
    """导出 Agent 友好的上下文"""
    from knoq.search import search as do_search
    from knoq.repository import list_entries
    from knoq.context import render_entries_json, render_entries_text
    from knoq.utils.console import info, error, console as console_print

    if format not in {"text", "json"}:
        error("输出格式必须是 text 或 json")
        raise typer.Exit(1)

    if query:
        results = do_search(query, limit=limit)
        entries = [r.entry for r in results]
    else:
        entries = list_entries(limit=limit)

    if not entries:
        info("无可导出的知识")
        return

    if format == "json":
        console_print.print(render_entries_json(entries, budget))
    else:
        console_print.print(render_entries_text(entries, budget))
