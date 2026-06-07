# knoq

> **knowledge + cli**：面向仓库的本地知识账本。用 SQLite + FTS5 保存项目事实、约定、决策和上下文，供人类和 AI Agent 稳定读取。

[![CI](https://github.com/FrozenYears/knoq/actions/workflows/ci.yml/badge.svg)](https://github.com/FrozenYears/knoq/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 特性

- 本地优先：默认在当前项目的 `.knoq/` 保存 SQLite 数据库，也支持 `KNOQ_HOME` 覆盖。
- CLI 可直接使用：添加、搜索、查看、更新、删除、扫描和导出知识条目。
- Agent 友好：内置 MCP stdio server，提供 `search_knowledge`、`get_topic`、`add_knowledge`、`export_context` 四个工具。
- 搜索双路径：ASCII 文本走 FTS5，CJK 文本使用安全转义的 LIKE fallback。
- 输出结构化：导出内容包含 `slug`、`tags`、`source`、`summary` 和正文，便于 Agent 精确引用。
- 安全边界：标题、内容、标签、路径、limit、budget 和 MCP request size 都有边界控制。
- 维护工具：`knoq optimize` 可重建 FTS 索引、执行 WAL checkpoint 和 ANALYZE。

## 安装

```bash
git clone https://github.com/FrozenYears/knoq.git
cd knoq
uv sync
```

开发环境使用 Python 3.13+。包管理推荐 `uv`。

## 快速开始

```bash
# 在当前项目初始化 .knoq/knoq.db
uv run knoq init

# 添加一条知识
uv run knoq add "部署流程" \
  -c "# 部署流程\n使用 Docker Compose 启动服务，命令为 docker compose up -d" \
  -t "deploy,docker"

# 搜索知识
uv run knoq search "Docker"
uv run knoq search "部署"

# 查看、更新、删除
uv run knoq list
uv run knoq show 部署流程-xxxxxx
uv run knoq update 部署流程-xxxxxx -c "# 部署流程\n已迁移到 K8s"
uv run knoq remove 部署流程-xxxxxx -f

# 扫描项目高价值文件
uv run knoq scan --dry-run

# 导出 Agent 上下文
uv run knoq export "Docker" --format text --budget 2000
uv run knoq export "Docker" --format json --budget 2000

# 数据库维护
uv run knoq optimize
```

## CLI 命令

| 命令 | 作用 |
| --- | --- |
| `knoq init` | 在当前目录初始化 `.knoq/` 数据目录 |
| `knoq add <title> -c <content> -t <tags>` | 添加知识条目 |
| `knoq search <query> --limit <n>` | 搜索知识，`limit` 范围为 1-100 |
| `knoq show <slug>` | 查看条目详情 |
| `knoq list --limit <n> --offset <n>` | 列出条目，`limit` 范围为 1-500 |
| `knoq update <slug> --title <title> -c <content> -t <tags>` | 更新条目 |
| `knoq remove <slug> -f` | 删除条目 |
| `knoq scan --dry-run` | 扫描 README、pyproject、package.json 等项目文件 |
| `knoq export <query> --format text/json --budget <n>` | 导出 Agent 上下文 |
| `knoq optimize` | 重建 FTS 索引并优化 SQLite |

## 数据与输入限制

- 内容长度：最大 100,000 字符。
- 标题长度：最大 500 字符，不能为空。
- 标签：最多 20 个，每个最长 64 字符。
- source path：最长 1,000 字符。
- scan：跳过符号链接和超过 1MB 的文件。
- MCP 单请求：最大 1MB。
- MCP 单响应：最大 500KB，超过会截断。

## AI Agent 集成

### MCP Server

knoq 内置纯标准库 JSON-RPC stdio MCP Server。当前默认协议版本为 `2025-11-25`，并兼容 `2025-06-18`、`2025-03-26`、`2024-11-05`。

工具列表：

| 工具 | 作用 |
| --- | --- |
| `search_knowledge` | 搜索本地知识库，返回标题、slug、tags、source、score 和 snippet |
| `get_topic` | 按 slug 获取完整条目 |
| `add_knowledge` | 添加知识条目 |
| `export_context` | 按 query/limit/budget 导出 Agent 上下文 |

### Claude Code

推荐使用 Claude Code CLI 一键写入完整 stdio 配置：

```powershell
claude mcp add-json --scope user knoq '{"type":"stdio","command":"uv","args":["--directory","<KNOQ_REPO_PATH>","run","python","-m","knoq.mcp_server"],"env":{}}'
```

其中 `<KNOQ_REPO_PATH>` 替换为你本机 `knoq` 仓库路径，例如 clone 后的项目目录。Windows 路径写进 JSON 时建议使用正斜杠，例如 `E:/path/to/knoq`；如果使用反斜杠，需要写成 `E:\\path\\to\\knoq`。若只想在当前项目生效，可以把 `--scope user` 改成 `--scope project`。添加后检查：

```powershell
claude mcp list
claude mcp get knoq
```

等价的手动 Claude Code 配置如下：

```json
{
  "mcpServers": {
    "knoq": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "<KNOQ_REPO_PATH>",
        "run",
        "python",
        "-m",
        "knoq.mcp_server"
      ],
      "env": {}
    }
  }
}
```

如果偏好普通 `add` 命令，也可以使用：

```powershell
claude mcp add knoq --scope user -- uv --directory <KNOQ_REPO_PATH> run python -m knoq.mcp_server
```

### Codex

推荐使用 Codex CLI 一键添加：

```powershell
codex mcp add knoq -- uv --directory <KNOQ_REPO_PATH> run python -m knoq.mcp_server
```

添加后检查：

```powershell
codex mcp list
codex mcp get knoq
```

也可以手动写入 Codex 配置：

```toml
[mcp_servers.knoq]
type = "stdio"
command = "uv"
args = ["--directory", "<KNOQ_REPO_PATH>", "run", "python", "-m", "knoq.mcp_server"]
```

### 手动验证

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2025-11-25"},"id":1}' | uv run python -m knoq.mcp_server
```

返回中应包含：

```json
{
  "protocolVersion": "2025-11-25",
  "capabilities": {
    "tools": {}
  }
}
```

## 使用场景

- 项目事实记录：部署流程、环境约定、故障处理、重要路径、账号申请流程。
- 架构决策记录：保留关键设计取舍，供后续人类和 Agent 查询。
- Agent Memory Layer：让 Claude Code、Codex、Cursor、Gemini CLI 等工具在工作前查询项目上下文。
- PR/Issue 支持：导出相关知识片段作为 review、修 bug 或写文档的上下文。
- 本地私有知识库：无需外部服务，适合敏感项目或离线场景。

## 技术栈

| 组件 | 选择 |
| --- | --- |
| 语言 | Python 3.13+ |
| CLI | Typer |
| 输出 | Rich |
| 存储 | SQLite |
| 搜索 | FTS5 + LIKE fallback |
| Agent 接入 | MCP JSON-RPC stdio |
| 测试 | pytest |

## 开发

```bash
uv sync
uv run pytest tests/ -v
```

当前测试覆盖 92 个用例，包括 CLI、SQLite、Markdown 扫描、MCP handler、MCP stdio 子进程流、路径解析、Repository 和 Search。

## 已知权衡

- CJK 搜索当前使用 LIKE fallback，数据量很大时会退化为逐行过滤。后续可评估 FTS5 trigram、预分词或 ICU tokenizer。
- MCP stdio 使用换行分隔 JSON，而不是 `Content-Length` framing；这与当前目标 Agent 使用方式一致，但接入其他客户端前应做兼容性验证。
- SQLite 单 writer 模型适合本地知识账本，高并发批量写入场景应增加重试或批处理。

## License

[MIT](LICENSE)
