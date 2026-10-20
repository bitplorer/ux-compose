"""Unit: product build CLI owns the Tailwind resolver."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

import pytest

from ux_compose.cli import main
from ux_compose.cli.product_build import find_product_root
from ux_compose.scaffold import create_app


def test_help_lists_build(capsys):
    assert main(["--help"]) == 0
    out = capsys.readouterr().out
    assert "uxcompose build" in out
    assert "create-app → serve dev → build → deploy" in out
    assert "CSS minify: uxcompose build" in out
    assert "ux_dom.cli.tailwind" not in out


def test_find_product_root_names_cwd_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    try:
        find_product_root()
    except FileNotFoundError as exc:
        msg = str(exc)
        assert "app.py" in msg
        assert str(tmp_path.resolve()) in msg
        assert "--app" in msg or "cd" in msg.lower()
    else:
        raise AssertionError("expected FileNotFoundError when cwd has no app.py")


def test_find_product_root_from_app_ref_dirname(tmp_path, monkeypatch):
    """uxcompose build --app path/to/app:asgi finds the create-app root."""
    dest = tmp_path / "shop"
    root = create_app(dest, name="shop")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    found = find_product_root(elsewhere, app_ref=f"{root / 'app'}:asgi")
    assert found == root.resolve()
    found_py = find_product_root(elsewhere, app_ref=f"{root / 'app.py'}:asgi")
    assert found_py == root.resolve()


def test_cli_build_cwd_error_is_clear(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    rc = main(["build", "--skip-tailwind", "--skip-import"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "app.py" in err
    assert str(tmp_path.resolve()) in err


def test_build_without_secret_is_one_clear_line(tmp_path, monkeypatch, capsys):
    """Fresh scaffold, DEBUG and secret unset: rc 1, no traceback."""
    root = create_app(tmp_path / "demo", name="demo")
    for name in ("DEBUG", "UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(root)
    rc = main(["build", "--skip-tailwind"])
    out = capsys.readouterr().out
    assert rc == 1
    assert (
        "[FAIL] import:app:asgi: Channel secret refused: attach() requires "
        "UX_CHANNEL_SECRET or UX_BEHAVIOR_SECRET outside dev; the public dev "
        "secret is not accepted\n"
    ) in out
    assert "Traceback" not in out
    assert "RuntimeError" not in out


@pytest.mark.parametrize(
    "env, reason",
    [
        (
            {"UX_CHANNEL_SECRET": "dev-secret-key-32chars-minimum!!!!"},
            "the public dev secret is not accepted\n",
        ),
        (
            {"DEBUG": "1", "REDIS_URL": "redis://127.0.0.1:1"},
            "attach() requires UX_CHANNEL_SECRET or "
            "UX_BEHAVIOR_SECRET when REDIS_URL is set; a per-process dev secret "
            "is not shared across processes\n",
        ),
    ],
)
def test_build_keeps_ux_behaviors_own_refusal(tmp_path, monkeypatch, capsys, env, reason):
    """A secret that is set but refused, or REDIS_URL with DEBUG=1: ux-behavior's reason."""
    root = create_app(tmp_path / "demo", name="demo")
    for name in ("DEBUG", "UX_CHANNEL_SECRET", "UX_BEHAVIOR_SECRET", "REDIS_URL"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    monkeypatch.chdir(root)
    rc = main(["build", "--skip-tailwind"])
    out = capsys.readouterr().out
    assert rc == 1
    assert f"[FAIL] import:app:asgi: Channel secret refused: {reason}" in out
    assert "Traceback" not in out
