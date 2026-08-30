"""A/X/Y routing policy — no live servers."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.devstack import CHANNEL_PREFIXES, RELOAD_EXCLUDES, RELOAD_INCLUDES, backend_for


def test_channel_paths_go_to_y():
    assert backend_for("/ux-channel") == "Y"
    assert backend_for("/ux-channel/action") == "Y"
    assert backend_for("/ux-channel/static/ux-channel.js") == "Y"


def test_pages_css_hmr_go_to_x():
    assert backend_for("/hello") == "X"
    assert backend_for("/css/output.css") == "X"
    assert backend_for("/__uxcompose/hmr") == "X"
    assert backend_for("/") == "X"


def test_reload_policy_ignores_css():
    assert "*.py" in RELOAD_INCLUDES
    assert "*.css" in RELOAD_EXCLUDES
    assert "assets/*" in RELOAD_EXCLUDES


def test_prefixes_are_narrow():
    assert CHANNEL_PREFIXES == ("/ux-channel",)


def test_cli_dev_uses_stack_not_only_factory():
    cli = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    assert "run_dev_stack" in cli
    assert "--single" in cli
    assert "hmr:asgi_factory" in cli
    assert "--watch=always" in cli
    assert "stdin=subprocess.DEVNULL" in cli


def test_hmr_module_still_has_no_watcher():
    src = (ROOT / "src" / "ux_compose" / "hmr.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "start_watcher" not in names
    assert "Popen" not in src
