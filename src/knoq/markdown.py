"""Markdown 元数据解析和扫描提取"""

import re
from pathlib import Path

MAX_SCAN_FILE_SIZE = 1_000_000


def extract_title(content: str, fallback: str = "untitled") -> str:
    """从 Markdown 内容提取标题（首个 # 标题）"""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else fallback


def extract_tags(content: str) -> list[str]:
    """从内容提取标签（#tag 格式，支持中文）"""
    return list(set(re.findall(r"(?:^|\s)#([\w][\w-]*)", content, re.UNICODE)))


def extract_summary(content: str, max_len: int = 200) -> str:
    """提取摘要：跳过标题行，取第一段文本"""
    lines = content.strip().split("\n")
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#"):
            return line[:max_len]
    return ""


# 常见项目文件及其提取规则
SCAN_TARGETS = {
    "README.md": "project-readme",
    "Makefile": "build-commands",
    "Dockerfile": "docker-config",
    "docker-compose.yml": "docker-compose",
    "pyproject.toml": "python-config",
    "package.json": "node-config",
    "Cargo.toml": "rust-config",
    ".env.example": "env-template",
}


def scan_project_files(root: Path) -> list[dict]:
    """扫描项目中的高价值文件，返回可导入的知识条目候选"""
    results = []
    for filename, category in SCAN_TARGETS.items():
        filepath = root / filename
        if filepath.exists() and filepath.is_file() and not filepath.is_symlink():
            try:
                if filepath.stat().st_size > MAX_SCAN_FILE_SIZE:
                    continue
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                if content.strip():
                    results.append({
                        "title": f"[{category}] {filename}",
                        "content": content[:2000],  # 限制长度
                        "source": str(filepath),
                        "tags": [category],
                    })
            except Exception:
                continue
    return results
