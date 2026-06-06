# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

knoq (knowledge + cli) — 面向仓库的本地 CLI 知识账本。用最少结构保存项目事实、约定、决策，供人和 AI Agent 读取。

## Commands

```bash
# 安装（开发模式）
uv sync

# 运行 CLI
uv run knoq init
uv run knoq add "标题" -c "内容" -t "标签"
uv run knoq search "关键词"
uv run knoq list
uv run knoq show <slug>
uv run knoq update <slug> -c "新内容"
uv run knoq remove <slug> -f
uv run knoq scan --dry-run
uv run knoq export "查询" --format json --budget 2000

# 测试
uv run pytest tests/ -v
uv run pytest tests/test_repository.py -v          # 单个文件
uv run pytest tests/test_repository.py::TestAddEntry -v  # 单个类

# MCP Server（stdio）
uv run python -m knoq.mcp_server
```

## Architecture

**数据流：** CLI 命令 → `repository.py` / `search.py` → SQLite (FTS5)

- `cli.py` — Typer 入口，9 个命令（init/add/update/search/show/list/remove/scan/export），每个命令用延迟导入避免启动开销
- `models.py` — `Entry` dataclass，含 `from_row()` 和 `to_dict()` 序列化方法，是唯一的数据传输对象
- `repository.py` — CRUD 操作，slug 由 title 正则生成，duplicate 用 `IntegrityError` → `ValueError` 转换
- `search.py` — FTS5 英文搜索 + LIKE CJK 回退（`_has_cjk` 检测），CJK 摘要用 `_make_snippet` 字符串定位
- `db.py` — SQLite 外部内容 FTS5 + 3 个触发器自动同步 `entries_fts`（INSERT/UPDATE/DELETE），无需手动同步
- `markdown.py` — 从 Markdown 提取 title/tags/summary，`scan_project_files` 扫描项目高价值文件
- `mcp_server.py` — 纯标准库实现的 MCP stdio JSON-RPC 服务器，4 个工具，`__main__` 时自动 init_db
- `paths.py` — 数据目录 `~/.knoq/`，环境变量 `KNOQ_HOME` 可覆盖

## Key Design Decisions

- **FTS sync via triggers** — 不在 repository.py 中手动写 entries_fts，由 db.py 的 AFTER INSERT/UPDATE/DELETE 触发器自动同步
- **CJK search fallback** — FTS5 `unicode61` tokenizer 对中文分词差，CJK 查询自动降级到 LIKE 模糊匹配
- **Entry.from_row** — 定义在 models.py 而非 search.py，避免 repository↔search 循环导入
- **Windows UTF-8** — `console.py` 在 Windows 上强制 `sys.stdout.reconfigure(encoding="utf-8")` 解决 GBK 编码问题

## Testing

`conftest.py` 用 `monkeypatch.setenv("KNOQ_HOME", tmp_path)` 让每个测试使用独立临时数据库，无需清理。
