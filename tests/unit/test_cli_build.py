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
    assert "create-app → build → serve → deploy" in out
    assert "ux_compose.tailwind" in out
    assert "ux_dom.cli.tailwind" not in out


def test_product_build_owns_the_resolver():
    src = (ROOT / "src" / "ux_compose" / "cli_build.py").read_text(encoding="utf-8")
    assert "from ux_compose.tailwind import" in src
    assert "ux_dom.cli.tailwind" not in src
    tw = (ROOT / "src" / "ux_compose" / "tailwind.py").read_text(encoding="utf-8")
    assert "def resolve_tailwind" in tw
    assert "def discover_css_io" in tw
    assert "def argv_with_io" in tw
    assert "_download_standalone" in tw


def test_find_product_root_rejects_showcase_main_py(tmp_path, monkeypatch):
    showcase = tmp_path / "show"
    (showcase / "app").mkdir(parents=True)
    (showcase / "app" / "main.py").write_text("# leftover\n", encoding="utf-8")
    monkeypatch.chdir(showcase)
    try:
        find_product_root()
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as e:
        assert "app.py" in str(e)
        assert "uxdom build" in str(e)


def test_build_honors_level_pin(tmp_path):
    from ux_compose.build import build

    root = create_app(tmp_path / "p", name="p", level=1)
    app, _asgi, _bundle = build(
        root, name="p", host="asgi", live="null", level=1, fail_closed=False
    )
    assert int(app.level) <= 1



def test_run_product_build_skip_tailwind(tmp_path, monkeypatch):
    root = create_app(tmp_path / "p", name="p")
    monkeypatch.chdir(root)
    report = run_product_build(cwd=root, skip_tailwind=True, skip_import=True)
    assert report.ok
    names = [s.name for s in report.steps]
    assert "app.py" in names
    assert "tailwind" in names


def test_cli_build_skip(tmp_path, monkeypatch, capsys):
    root = create_app(tmp_path / "p", name="p")
    monkeypatch.chdir(root)
    rc = main(["build", "--skip-tailwind", "--skip-import"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "BUILD OK" in out
    assert "uxcompose build" in out
