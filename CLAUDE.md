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
uv run knoq optimize             # 重建 FTS 索引 + WAL checkpoint + ANALYZE

# 测试
uv run pytest tests/ -v
uv run pytest tests/test_repository.py -v
uv run pytest tests/test_repository.py::TestAddEntry -v

# MCP Server
uv run python -m knoq.mcp_server
```

## Architecture

**数据流：** CLI/MCP → `repository.py` / `search.py` → SQLite (FTS5)

- `cli.py` — Typer 入口，10 个命令（含 optimize）+ `--version`，每个命令延迟导入
- `models.py` — `Entry` dataclass，含 `from_row()` / `to_dict()`
- `repository.py` — CRUD + 内容长度限制（100KB） + CJK slug（原始字符 + hash 后缀）+ 错误处理
- `search.py` — FTS5 英文搜索（`_sanitize_fts_query`）+ LIKE CJK 回退（`_escape_like`）
- `db.py` — FTS5 external content + 触发器 + PRAGMA 优化 + schema 迁移 + optimize/rebuild
- `markdown.py` — 提取 title/tags/summary，扫描项目高价值文件
- `mcp_server.py` — 纯标准库 MCP stdio 服务器，4 个工具 + 输入验证 + 响应截断（500KB）
- `paths.py` — 数据目录优先级：`KNOQ_HOME` → 项目内 `.knoq/` → `~/.knoq`

## Key Design Decisions

- **项目级数据目录** — `knoq init` 在当前目录创建 `.knoq/`，`paths.py` 从 cwd 向上查找 `.knoq` 或 `.git` 确定项目根
- **SQLite PRAGMA 优化** — WAL + busy_timeout=5000 + synchronous=NORMAL + recursive_triggers=ON + temp_store=MEMORY（参考 simonw/sqlite-utils、rtk-ai/rtk 最佳实践）
- **FTS5 sync via triggers** — 3 个触发器自动同步，`knoq optimize` 命令做 rebuild + WAL checkpoint + ANALYZE（解决 _fts_docsize 膨胀问题）
- **Schema 迁移** — PRAGMA user_version 跟踪版本，MIGRATIONS 字典定义增量 SQL（参考 rtk 的自动迁移模式）
- **CJK 双路径搜索** — CJK 文本用 LIKE（`_escape_like` 转义 `%`/`_`），ASCII 用 FTS5（`_sanitize_fts_query` 清理特殊字符）
- **MCP 安全** — 输入验证（`_require`）、类型强制、长度限制、响应截断 500KB、异常脱敏（不暴露内部路径）

## Testing

- `conftest.py` 用 `monkeypatch.setenv("KNOQ_HOME", tmp_path)` 隔离数据库
- CLI 测试用 `monkeypatch.chdir(tmp_path)` 隔离项目目录（防止 `.knoq/` 污染项目根）
- 70 个测试：cli(14) + db(5) + markdown(9) + mcp_server(8) + paths(6) + repository(14) + search(11) + special_chars(3)

## Known Issues & Gotchas

以下来自社区调研（simonw/sqlite-utils、rtk-ai/rtk、modelcontextprotocol/python-sdk 的 issue）和两轮内部审计：

### SQLite / FTS5
- **FTS5 detail=column 不支持短语查询** — 已使用 `detail=full`。如果未来需要节省索引空间改用 `detail=column`/`detail=none`，需同时修改搜索逻辑避免隐式短语查询
- **FTS5 _fts_docsize 膨胀** — 频繁 UPDATE/DELETE 会积累垃圾行。`knoq optimize` 做 `rebuild` 清理。参考 sqlite-utils #149
- **recursive_triggers 必须开启** — 否则 INSERT OR REPLACE 时触发器不触发，FTS 索引不一致。参考 sqlite-utils #155
- **VACUUM 时 /tmp 空间** — 已设 `temp_store=MEMORY` 避免。参考 sqlite-utils #430

### MCP Server
- **stdio 传输用 NDJSON（换行分隔 JSON）** — 与 Content-Length 格式不兼容，但与 Claude Code / Codex 一致。参考 MCP SDK #2546
- **响应截断 500KB** — 防止 Agent 上下文窗口溢出。参考 MCP SDK #144
- **长时间运行后可能无响应** — MCP SDK 的 anyio 内存流问题，knoq 的简单 stdio 实现不依赖 anyio，影响较小。参考 MCP SDK #1333

### Windows
- **Rich 编码** — `console.py` 在 Windows 上强制 UTF-8 输出。Python 3.15 将默认启用 UTF-8 模式（PEP 686），届时可移除。参考 Rich #3388
- **MSIX/AppContainer 路径** — Windows 文件系统虚拟化可能重定向数据库路径，用 `KNOQ_HOME` 环境变量覆盖。参考 rtk #1577

## Repo Conventions

- 提交信息：`类型: 简述`（feat/fix/docs/test/refactor）
- 分支：`main`
- CI：GitHub Actions（`uv run pytest tests/ -v`）
- License：MIT
