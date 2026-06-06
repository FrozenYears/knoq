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

### MCP Server（规划中）
提供 `search_knowledge`、`get_topic`、`add_knowledge`、`export_context` 四个工具。

## 技术栈

- Python 3.13+
- Typer (CLI)
- SQLite + FTS5 (存储和搜索)
- Rich (终端输出)

## License

MIT
