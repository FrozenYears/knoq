# knoq

> **knowledge + cli** — 面向仓库的本地知识账本

[![CI](https://github.com/FrozenYears/knoq/actions/workflows/ci.yml/badge.svg)](https://github.com/FrozenYears/knoq/actions/workflows/ci.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

用最少结构保存项目中的事实、约定、决策、术语，供人和 AI Agent 稳定读取。

## 安装

```bash
git clone https://github.com/FrozenYears/knoq.git
cd knoq
uv sync
```

## 快速开始

```bash
# 初始化
knoq init

# 添加知识
knoq add "部署流程" -c "# 部署\n使用 Docker，运行 docker compose up" -t "deploy,docker"

# 搜索（支持中英文）
knoq search "Docker"
knoq search "部署"

# 列出 / 查看 / 更新 / 删除
knoq list
knoq show 部署流程
knoq update 部署流程 -c "# 部署\n已迁移到 K8s"
knoq remove 部署流程 -f

# 扫描项目自动提取
knoq scan --dry-run

# 导出 Agent 上下文
knoq export "Docker" --format json --budget 2000
```

## 命令

| 命令 | 功能 |
|------|------|
| `knoq init` | 初始化知识库 |
| `knoq add <title> -c <content> -t <tags>` | 添加条目 |
| `knoq search <query>` | 搜索知识 |
| `knoq show <slug>` | 查看详情 |
| `knoq list` | 列出条目 |
| `knoq update <slug> -c <content>` | 更新条目 |
| `knoq remove <slug>` | 删除条目 |
| `knoq scan` | 扫描项目文件 |
| `knoq export <query>` | 导出 Agent 上下文 |

## AI Agent 集成

### MCP Server

内置 MCP stdio 服务器，提供 `search_knowledge`、`get_topic`、`add_knowledge`、`export_context` 四个工具。

**Claude Code：**

```json
{
  "mcpServers": {
    "knoq": {
      "command": "uv",
      "args": ["run", "python", "-m", "knoq.mcp_server"]
    }
  }
}
```

**Codex：**

```toml
[mcp_servers.knoq]
type = "stdio"
command = "uv"
args = ["run", "python", "-m", "knoq.mcp_server"]
```

**手动测试：**

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | uv run python -m knoq.mcp_server
```

## 技术栈

| 组件 | 选择 |
|------|------|
| 语言 | Python 3.13+ |
| CLI | Typer |
| 存储 | SQLite + FTS5 |
| 输出 | Rich |
| MCP | 纯标准库 JSON-RPC stdio |

零外部服务依赖，仅需 Python。

## 开发

```bash
uv sync
uv run pytest tests/ -v
```

## License

[MIT](LICENSE)
