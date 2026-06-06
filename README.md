# knoq

> **knowledge + cli** — 面向仓库的本地知识账本

[![Tests](https://img.shields.io/badge/tests-43%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-≥3.13-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

用最少结构保存"事实、约定、决策、命令、术语、模块摘要"，并能被人和 AI Agent 稳定读取。

## 安装

```bash
git clone https://github.com/YOUR_USERNAME/knoq.git
cd knoq
uv sync
```

## 快速开始

```bash
# 初始化知识库
knoq init

# 添加知识条目
knoq add "部署流程" -c "# 部署\n使用 Docker 部署，运行 docker compose up" -t "deploy,docker"

# 搜索（支持中英文）
knoq search "Docker"
knoq search "部署"

# 列出所有条目
knoq list

# 查看详情
knoq show 部署流程

# 更新条目
knoq update 部署流程 -c "# 部署\n已迁移到 K8s"

# 扫描项目自动提取知识
knoq scan --dry-run

# 导出 Agent 友好的上下文
knoq export "Docker" --format json --budget 2000
```

## 命令列表

| 命令 | 功能 | 示例 |
|------|------|------|
| `knoq init` | 初始化知识库 | `knoq init` |
| `knoq add <title>` | 添加条目 | `knoq add "标题" -c "内容" -t "标签"` |
| `knoq search <query>` | 搜索知识 | `knoq search "关键词"` |
| `knoq show <slug>` | 查看详情 | `knoq show 标题` |
| `knoq list` | 列出条目 | `knoq list --limit 20` |
| `knoq update <slug>` | 更新条目 | `knoq update 标题 -c "新内容"` |
| `knoq remove <slug>` | 删除条目 | `knoq remove 标题 -f` |
| `knoq scan` | 扫描项目 | `knoq scan --dry-run` |
| `knoq export` | 导出上下文 | `knoq export "查询" --format json` |

## 与 AI Agent 集成

### MCP Server

knoq 内置 MCP stdio 服务器，提供 4 个工具：

| 工具 | 功能 |
|------|------|
| `search_knowledge` | 搜索本地知识库 |
| `get_topic` | 获取条目详情 |
| `add_knowledge` | 添加知识条目 |
| `export_context` | 导出 Agent 上下文 |

**Claude Code 配置：**

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

**Codex 配置：**

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

- Python 3.13+
- Typer (CLI)
- SQLite + FTS5 (存储和全文搜索)
- Rich (终端输出)
- 零外部服务依赖

## 开发

```bash
uv sync
uv run pytest tests/ -v
```

## License

MIT
