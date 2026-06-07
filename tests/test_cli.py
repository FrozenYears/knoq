"""CLI 命令集成测试"""

import os
from typer.testing import CliRunner
from knoq.cli import app

runner = CliRunner()


class TestVersion:
    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "knoq" in result.output
        assert "0.1.0" in result.output


class TestInit:
    def test_init_creates_db(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        result = runner.invoke(app, ["init"])
        assert result.exit_code == 0
        assert "已初始化" in result.output


class TestAdd:
    def test_add_with_content(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["add", "测试标题", "-c", "测试内容", "-t", "a,b"])
        assert result.exit_code == 0
        assert "已添加" in result.output

    def test_add_duplicate(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        runner.invoke(app, ["add", "重复", "-c", "内容"])
        result = runner.invoke(app, ["add", "重复", "-c", "内容2"])
        assert result.exit_code == 1


class TestSearch:
    def test_search_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        runner.invoke(app, ["add", "Docker指南", "-c", "使用 Docker 部署"])
        result = runner.invoke(app, ["search", "Docker"])
        assert result.exit_code == 0

    def test_search_cjk(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        runner.invoke(app, ["add", "部署指南", "-c", "部署流程说明"])
        result = runner.invoke(app, ["search", "部署"])
        assert result.exit_code == 0

    def test_search_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["search", "xyznonexistent"])
        assert result.exit_code == 0

    def test_search_rejects_zero_limit(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["search", "Docker", "--limit", "0"])
        assert result.exit_code != 0


class TestList:
    def test_empty_list(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["list"])
        assert result.exit_code == 0

    def test_rejects_negative_offset(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["list", "--offset", "-1"])
        assert result.exit_code != 0


class TestShow:
    def test_show_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["show", "不存在"])
        assert result.exit_code == 1


class TestUpdate:
    def test_update_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["update", "不存在", "-c", "新内容"])
        assert result.exit_code == 1


class TestRemove:
    def test_remove_not_found(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["remove", "不存在", "-f"])
        assert result.exit_code == 1


class TestExport:
    def test_export_empty(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["export"])
        assert result.exit_code == 0

    def test_export_with_entries(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        runner.invoke(app, ["add", "导出测试", "-c", "导出内容"])
        result = runner.invoke(app, ["export", "导出"])
        assert result.exit_code == 0
        assert "slug:" in result.output

    def test_export_json_includes_agent_metadata(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        runner.invoke(app, ["add", "JSON导出测试", "-c", "导出内容", "-t", "agent"])
        result = runner.invoke(app, ["export", "--format", "json"])
        assert result.exit_code == 0
        assert '"slug"' in result.output
        assert '"summary"' in result.output

    def test_export_rejects_invalid_format(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["export", "--format", "xml"])
        assert result.exit_code == 1


class TestScan:
    def test_scan_dry_run(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        runner.invoke(app, ["init"])
        result = runner.invoke(app, ["scan", "--dry-run"])
        assert result.exit_code == 0
