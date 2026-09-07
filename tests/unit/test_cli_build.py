"""Unit: product build CLI owns the Tailwind resolver."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main
from ux_compose.cli_build import find_product_root, run_product_build
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
