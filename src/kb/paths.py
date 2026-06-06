"""统一管理数据目录和文件路径"""

import os
from pathlib import Path


def home() -> Path:
    """获取 .kb 数据目录，默认 ~/.kb"""
    return Path(os.environ.get("KB_HOME", Path.home() / ".kb"))


def db_path() -> Path:
    """SQLite 数据库路径"""
    return home() / "kb.db"


def ensure_home() -> None:
    """确保数据目录存在"""
    home().mkdir(parents=True, exist_ok=True)
