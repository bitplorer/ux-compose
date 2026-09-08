"""Unit: deploy prepare checklist without writing project tree."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.deploy import _DOCKERFILE, format_deploy_result, prepare_deploy


def test_checklist_needs_app_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        prepare_deploy("checklist")


def test_checklist_with_app_py(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    result = prepare_deploy("checklist")
    assert result.provider == "checklist"
    assert result.instructions
    text = format_deploy_result(result)
    assert "uxcompose deploy" in text or "provider" in text


def test_dockerfile_relies_on_honest_requirements_txt():
    """Image install is pip -r only — no bare PyPI ux-* names."""
    assert "pip install --no-cache-dir -r requirements.txt" in _DOCKERFILE
    assert "ux-compose ux-dom ux-behavior" not in _DOCKERFILE
    assert "FROM python:3.14-slim" in _DOCKERFILE
