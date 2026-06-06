# Contributing to knoq

感谢你对 knoq 的兴趣！

## 开发环境

```bash
git clone https://github.com/FrozenYears/knoq.git
cd knoq
uv sync
```

## 运行测试

```bash
uv run pytest tests/ -v
```

## 提交规范

提交信息使用英文，格式：`类型: 简述`

- `feat:` 新功能
- `fix:` 修复
- `docs:` 文档
- `test:` 测试
- `refactor:` 重构

## Pull Request

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feat/my-feature`
3. 确保测试通过：`uv run pytest tests/ -v`
4. 提交 PR
