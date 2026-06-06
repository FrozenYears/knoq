"""测试配置：使用临时数据库"""

import os
import tempfile
import pytest


@pytest.fixture(autouse=True)
def tmp_kb_home(tmp_path, monkeypatch):
    """每个测试使用独立的临时 .kb 目录"""
    kb_home = tmp_path / ".kb"
    kb_home.mkdir()
    monkeypatch.setenv("KB_HOME", str(kb_home))
    # 重新初始化数据库
    from kb.db import init_db
    init_db()
    yield
