# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

knoq (knowledge + cli) — 面向仓库的本地 CLI 知识账本。用最少结构保存项目事实、约定、决策，供人和 AI Agent 读取。

## Commands

```bash
uv sync                          # 安装依赖
uv run knoq --version            # 版本号
uv run knoq init                 # 初始化（在当前目录创建 .knoq/）
uv run knoq add "标题" -c "内容" -t "标签"
uv run knoq search "关键词"
uv run knoq list / show / update / remove
uv run knoq scan --dry-run
uv run knoq export "查询" --format json --budget 2000

# 测试
uv run pytest tests/ -v
uv run pytest tests/test_repository.py -v
uv run pytest tests/test_repository.py::TestAddEntry -v

# MCP Server
uv run python -m knoq.mcp_server
```

## Architecture

**数据流：** CLI/MCP → `repository.py` / `search.py` → SQLite (FTS5)

- `cli.py` — Typer 入口，9 个命令 + `--version` 标志，每个命令延迟导入
- `models.py` — `Entry` dataclass，含 `from_row()` / `to_dict()`
- `repository.py` — CRUD + 内容长度限制（100KB） + CJK slug（原始字符 + hash 后缀）+ 错误处理（`sqlite3.Error` → `ValueError`）
- `search.py` — FTS5 英文搜索（`_sanitize_fts_query` 清理特殊字符）+ LIKE CJK 回退（`_escape_like` 转义 `%`/`_`）
- `db.py` — FTS5 external content + 触发器自动同步 + `busy_timeout=5000` + WAL
- `markdown.py` — 提取 title/tags/summary，扫描项目高价值文件
- `mcp_server.py` — 纯标准库 MCP stdio 服务器，4 个工具 + 输入验证（`_require` + 类型转换 + 长度上限）
- `paths.py` — 数据目录优先级：`KNOQ_HOME` 环境变量 → 项目内 `.knoq/`（向上查找 `.knoq` 或 `.git`）→ `~/.knoq`

## Key Design Decisions

- **项目级数据目录** — `knoq init` 在当前目录创建 `.knoq/`，`paths.py` 从 cwd 向上查找 `.knoq` 或 `.git` 确定项目根
- **FTS sync via triggers** — 3 个触发器自动同步 `entries_fts`，repository.py 不手动写 FTS
- **CJK 双路径搜索** — CJK 文本用 LIKE（`_escape_like` 转义通配符），ASCII 用 FTS5（`_sanitize_fts_query` 清理特殊字符）
- **CJK slug** — 包含非 ASCII 字符时追加 md5[:6] 短 hash 保证唯一性
- **MCP 安全** — 输入验证（`_require`）、类型强制转换、内容长度上限、异常消息脱敏（不暴露内部路径）

## Testing

- `conftest.py` 用 `monkeypatch.setenv("KNOQ_HOME", tmp_path)` 隔离数据库
- CLI 测试用 `monkeypatch.chdir(tmp_path)` 隔离项目目录
- 65 个测试覆盖：repository(14) + search(11) + markdown(9) + mcp_server(8) + paths(6) + cli(14) + special_chars(3)

## Repo Conventions

- 提交信息：`类型: 简述`（feat/fix/docs/test/refactor）
- 分支：`main`
- CI：GitHub Actions（`uv run pytest tests/ -v`）
- License：MIT
