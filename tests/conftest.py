"""测试配置：使用临时数据库"""

import os
import tempfile
import pytest


@pytest.fixture(autouse=True)
def tmp_knoq_home(tmp_path, monkeypatch):
    """每个测试使用独立的临时 .knoq 目录"""
    knoq_home = tmp_path / ".knoq"
    knoq_home.mkdir()
    monkeypatch.setenv("KNOQ_HOME", str(knoq_home))
    from knoq.db import init_db
    init_db()
    yield
