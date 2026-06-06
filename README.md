# kb - 本地知识库 CLI

面向仓库的本地 CLI 知识账本。用最少结构保存"事实、约定、决策、命令、术语、模块摘要"，并能被人和 AI Agent 稳定读取。

## 安装

```bash
uv pip install -e .
```

## 快速开始

```bash
# 初始化知识库
kb init

# 添加知识条目
kb add "部署流程" -c "# 部署\n使用 Docker 部署，运行 docker compose up" -t "deploy,docker"

# 搜索
kb search "Docker"
kb search "部署"

# 列出所有条目
kb list

# 查看详情
kb show 部署流程

# 扫描项目自动提取知识
kb scan --dry-run

# 导出 Agent 友好的上下文
kb export "Docker" --format json --budget 2000
```

## 命令列表

| 命令 | 功能 | 示例 |
|------|------|------|
| `kb init` | 初始化知识库 | `kb init` |
| `kb add <title>` | 添加条目 | `kb add "标题" -c "内容" -t "标签"` |
| `kb search <query>` | 搜索知识 | `kb search "关键词"` |
| `kb show <slug>` | 查看详情 | `kb show 标题` |
| `kb list` | 列出条目 | `kb list --limit 20` |
| `kb update <slug>` | 更新条目 | `kb update 标题 -c "新内容"` |
| `kb remove <slug>` | 删除条目 | `kb remove 标题 -f` |
| `kb scan` | 扫描项目 | `kb scan --dry-run` |
| `kb export` | 导出上下文 | `kb export "查询" --format json` |

## 与 AI Agent 集成

### CLI 子命令
```bash
# Agent 可直接调用
kb search "项目怎么启动"
kb export "auth" --budget 1500
kb scan --changed
```

### MCP Server

kb 内置 MCP stdio 服务器，提供 4 个工具：

| 工具 | 功能 |
|------|------|
| `search_knowledge` | 搜索本地知识库 |
| `get_topic` | 获取条目详情 |
| `add_knowledge` | 添加知识条目 |
| `export_context` | 导出 Agent 上下文 |

**在 Claude Code 中配置：**

```json
// .claude/settings.json
{
  "mcpServers": {
    "kb": {
      "command": "uv",
      "args": ["run", "python", "-m", "kb.mcp_server"],
      "cwd": "/path/to/your/project"
    }
  }
}
```

**在 Codex 中配置：**

```toml
# ~/.codex/config.toml
[mcp_servers.kb]
type = "stdio"
command = "uv"
args = ["run", "python", "-m", "kb.mcp_server"]
```

**手动测试：**

```bash
echo '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}' | uv run python -m kb.mcp_server
```

## 技术栈

- Python 3.13+
- Typer (CLI)
- SQLite + FTS5 (存储和搜索)
- Rich (终端输出)

## License

MIT
