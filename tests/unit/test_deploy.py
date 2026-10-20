"""Unit: deploy prepare checklist without writing project tree."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.cli.deploy import _DOCKERFILE, format_deploy_result, prepare_deploy


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


_PROVIDERS = ("docker", "fly", "render", "railway", "vps")


def _app(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")


def test_render_generates_the_secret_on_render(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    prepare_deploy("render", app_name="demo")
    text = (tmp_path / "render.yaml").read_text(encoding="utf-8")
    assert "      - key: UX_CHANNEL_SECRET\n        generateValue: true\n" in text
    assert "DEBUG" not in text


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_every_provider_declares_the_secret_without_a_value(tmp_path, monkeypatch, provider):
    _app(tmp_path, monkeypatch)
    secret = "never-in-a-file-0123456789"
    monkeypatch.setenv("UX_CHANNEL_SECRET", secret)
    result = prepare_deploy(provider, app_name="demo")
    told = format_deploy_result(result)
    written = "".join(
        (tmp_path / name).read_text(encoding="utf-8") for name in result.files_written
    )
    assert "UX_CHANNEL_SECRET" in told + written
    assert secret not in told + written
    assert not any(
        line.split("UX_CHANNEL_SECRET=", 1)[1][:1].isalnum()
        for line in (told + written).splitlines()
        if "UX_CHANNEL_SECRET=" in line
    ), "a literal secret value was written"


def test_vps_unit_reads_an_environment_file(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    result = prepare_deploy("vps", app_name="demo")
    unit = (tmp_path / "deploy" / "demo.service").read_text(encoding="utf-8")
    assert "EnvironmentFile=/etc/demo.env\n" in unit
    assert "sudo install -m 600 /dev/null /etc/demo.env" in result.instructions
    assert any(step.endswith("| sudo tee /etc/demo.env >/dev/null") for step in result.instructions)


def test_checklist_names_the_secret(tmp_path, monkeypatch):
    _app(tmp_path, monkeypatch)
    result = prepare_deploy("checklist")
    assert any(
        "Set UX_CHANNEL_SECRET (≥16 chars, never commit it)" in step
        for step in result.instructions
    )
