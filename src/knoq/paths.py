"""统一管理数据目录和文件路径

优先级：
1. KNOQ_HOME 环境变量（显式覆盖）
2. 项目根目录下的 .knoq/（从 cwd 向上查找 .knoq 或 .git）
3. ~/.knoq（全局 fallback）
"""

import os
from pathlib import Path


def _find_project_root() -> Path | None:
    """从当前目录向上查找 .knoq/ 或 .git/ 目录，确定项目根目录"""
    current = Path.cwd().resolve()
    for parent in [current, *current.parents]:
        if (parent / ".knoq").is_dir():
            return parent
        if (parent / ".git").is_dir():
            return parent
    return None


def home() -> Path:
    """获取数据目录"""
    env_home = os.environ.get("KNOQ_HOME")
    if env_home:
        return Path(env_home)

    project_root = _find_project_root()
    if project_root:
        return project_root / ".knoq"

    return Path.home() / ".knoq"


def db_path() -> Path:
    """SQLite 数据库路径"""
    return home() / "knoq.db"


def ensure_home() -> None:
    """确保数据目录存在"""
    home().mkdir(parents=True, exist_ok=True)
