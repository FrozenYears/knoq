# CLAUDE.md

This file gives Claude Code and other coding agents the minimum project context needed to work safely in this repository.

## Project

`knoq` means **knowledge + cli**. It is a local knowledge ledger for code repositories.

The project stores facts, conventions, decisions, runbooks, and reusable context in a local SQLite database so humans and AI Agents can query accurate project knowledge before acting.

## Commands

```bash
uv sync
uv run knoq --version
uv run knoq init
uv run knoq add "标题" -c "内容" -t "tag1,tag2"
uv run knoq search "关键词" --limit 20
uv run knoq list --limit 50 --offset 0
uv run knoq show <slug>
uv run knoq update <slug> -c "新内容"
uv run knoq remove <slug> -f
uv run knoq scan --dry-run
uv run knoq export "查询" --format json --budget 2000
uv run knoq optimize

# Tests
uv run pytest tests/ -v
uv run pytest tests/test_mcp_server.py -v

# MCP Server
uv run python -m knoq.mcp_server
```

## Architecture

Data flow:

```text
CLI / MCP Server
  -> repository.py / search.py / context.py
  -> db.py
  -> SQLite entries + entries_fts
```

Modules:

- `cli.py`: Typer CLI entrypoint. User-facing command validation lives here where possible.
- `mcp_server.py`: JSON-RPC stdio MCP server with four tools: `search_knowledge`, `get_topic`, `add_knowledge`, `export_context`.
- `repository.py`: CRUD, slug generation, content hash, input validation, and SQLite writes.
- `search.py`: ASCII FTS5 search and CJK LIKE fallback.
- `context.py`: Shared Agent-friendly rendering for CLI export and MCP responses.
- `db.py`: SQLite connection, PRAGMA setup, schema, migrations, FTS triggers, optimize/rebuild.
- `markdown.py`: title/tag/summary extraction and project-file scan candidates.
- `paths.py`: data directory resolution: `KNOQ_HOME` -> project `.knoq/` -> `~/.knoq`.
- `models.py`: `Entry` dataclass and row/dict conversion.
- `utils/console.py`: Rich console output and Windows UTF-8 handling.

## Current Behavior

- Database defaults to project-local `.knoq/knoq.db` after `knoq init`.
- `KNOQ_HOME` overrides the data directory and is used heavily in tests.
- SQLite uses WAL, `busy_timeout=5000`, `synchronous=NORMAL`, `recursive_triggers=ON`, `temp_store=MEMORY`, and foreign keys.
- FTS5 uses external content mode with insert/update/delete triggers.
- `knoq optimize` runs FTS rebuild, FTS optimize, WAL checkpoint, and ANALYZE.
- ASCII search uses FTS5 MATCH with quoted terms to avoid reserved-word failures.
- CJK search uses escaped LIKE fallback.
- CLI export and MCP responses share `context.py` so Agents receive consistent `slug/tags/source/summary/content` output.

## Input Limits

Keep these limits consistent between `repository.py`, `cli.py`, and `mcp_server.py`:

- content: 100,000 characters
- title: 500 characters, non-empty
- tags: max 20
- tag length: 64 characters
- source path: 1,000 characters
- CLI search/export limit: 1-100
- CLI list limit: 1-500
- export budget: 100-100,000 characters
- MCP request: 1MB
- MCP response: 500KB
- scan file size: 1MB

## MCP Notes

Default MCP protocol version is `2025-11-25`. The server also accepts `2025-06-18`, `2025-03-26`, and `2024-11-05` during initialize.

Tool schemas include bounds and `additionalProperties: false`.

Malformed requests should never crash the server:

- non-object request -> `-32600`
- non-object params -> `-32600`
- non-object tool arguments -> `-32600`
- invalid tool argument values -> `-32602`
- unknown method/tool -> `-32601`

`tests/test_mcp_server.py::TestMcpStdio::test_stdio_agent_flow` verifies the real stdio subprocess flow.

## Testing

Current baseline: 92 tests.

Coverage areas:

- CLI integration
- SQLite schema, PRAGMA, optimize, migrations
- Markdown extraction and scan limits
- MCP handler and MCP stdio subprocess flow
- path resolution
- repository CRUD and input limits
- search FTS/CJK/special-character behavior

Run the full suite after behavior changes:

```bash
uv run pytest tests/ -v
```

## Known Tradeoffs

### CJK Search

CJK search currently uses `LIKE '%query%'` with escaping. This is simple and accurate enough for small local ledgers, but it can degrade at large scale because it filters rows rather than using a full-text index.

Future options:

- FTS5 trigram tokenizer
- pre-tokenized CJK terms
- ICU tokenizer
- external tokenizer such as jieba
- hybrid lexical + vector search

### SQLite Concurrency

WAL supports concurrent readers and one writer. This is appropriate for a local CLI knowledge ledger. For heavy concurrent write loads, add retry/backoff or batch writes in explicit transactions.

### MCP Framing

The current server uses newline-delimited JSON over stdio. It is intentionally simple and works with the target local Agent workflow. Verify framing before integrating with clients that require `Content-Length`.

## Repo Conventions

- Always communicate with the user in Chinese.
- Package manager: `uv`.
- Keep changes surgical and consistent with existing style.
- Prefer simple code over speculative abstraction.
- Add tests for bug fixes and boundary behavior.
- Commit message format: English, `type: summary`.
- Main branch: `main`.
- CI command: `uv run pytest tests/ -v`.

## Recent Important Changes

- `2c7d7e1 fix: improve cli and mcp agent usability`
  - stricter CLI bounds
  - Agent-friendly context rendering
  - MCP protocol negotiation and request validation
  - repository input validation
  - scan file-size/symlink guard
  - MCP stdio integration test
- `89e0774 fix: harden search and migration edge cases`
  - FTS reserved-word search hardening
  - negative limit handling
  - schema migration execution fix
