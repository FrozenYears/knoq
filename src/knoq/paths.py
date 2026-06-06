"""统一管理数据目录和文件路径"""

import os
from pathlib import Path


def home() -> Path:
    """获取 .knoq 数据目录，默认 ~/.knoq"""
    return Path(os.environ.get("KNOQ_HOME", Path.home() / ".knoq"))


def db_path() -> Path:
    """SQLite 数据库路径"""
    return home() / "knoq.db"


def ensure_home() -> None:
    """确保数据目录存在"""
    home().mkdir(parents=True, exist_ok=True)
