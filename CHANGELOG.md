# Changelog

## [0.1.0] - 2026-06-06

### Added
- 10 个 CLI 命令：init, add, update, search, show, list, remove, scan, export, optimize
- `--version` 标志
- SQLite + FTS5 全文搜索，CJK 中文搜索支持（LIKE 回退 + 通配符转义）
- MCP stdio 服务器（4 个工具 + 输入验证 + 响应截断 500KB + 异常脱敏）
- 项目级数据目录（`.knoq/` 在项目内，类似 `.git`）
- CJK slug 支持（原始字符 + 短 hash）
- 内容长度限制（100KB）
- 并发安全（WAL + busy_timeout + synchronous=NORMAL + recursive_triggers）
- Schema 版本迁移（PRAGMA user_version）
- 数据库优化命令（FTS5 rebuild + WAL checkpoint + ANALYZE）
- 项目文件自动扫描提取知识
- Agent 友好的上下文导出（text/json）
- 70 个单元测试（含 CLI 集成测试）
