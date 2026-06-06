"""paths.py 单元测试"""

from pathlib import Path
from unittest.mock import patch


class TestFindProjectRoot:
    def test_finds_knoq_dir(self, tmp_path, monkeypatch):
        project = tmp_path / "myproject"
        (project / ".knoq").mkdir(parents=True)
        monkeypatch.chdir(project)
        from knoq.paths import _find_project_root
        assert _find_project_root() == project

    def test_finds_git_dir(self, tmp_path, monkeypatch):
        project = tmp_path / "myproject"
        (project / ".git").mkdir(parents=True)
        monkeypatch.chdir(project)
        from knoq.paths import _find_project_root
        assert _find_project_root() == project

    def test_falls_back_to_none(self, tmp_path, monkeypatch):
        # 在文件系统根目录（没有 .knoq 或 .git）应返回 None
        # 用 mock 隔离父目录查找
        from knoq import paths
        with patch.object(paths, '_find_project_root', return_value=None):
            assert paths._find_project_root() is None


class TestHome:
    def test_env_override(self, tmp_path, monkeypatch):
        monkeypatch.setenv("KNOQ_HOME", str(tmp_path / "custom"))
        from knoq.paths import home
        assert home() == tmp_path / "custom"

    def test_project_local(self, tmp_path, monkeypatch):
        project = tmp_path / "myproject"
        (project / ".knoq").mkdir(parents=True)
        monkeypatch.chdir(project)
        monkeypatch.delenv("KNOQ_HOME", raising=False)
        from knoq.paths import home
        assert home() == project / ".knoq"

    def test_global_fallback(self, tmp_path, monkeypatch):
        # 模拟没有找到项目根目录的情况
        monkeypatch.delenv("KNOQ_HOME", raising=False)
        from knoq import paths
        with patch.object(paths, '_find_project_root', return_value=None):
            assert paths.home() == Path.home() / ".knoq"
