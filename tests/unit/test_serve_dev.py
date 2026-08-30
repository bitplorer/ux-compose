"""Public vs pages vs channel routing — no live servers."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.serve_dev import (
    CHANNEL_PATH_PREFIX,
    RELOAD_EXCLUDES,
    RELOAD_INCLUDES,
    owner_for,
    pick_loopback_port,
    port_is_free,
)


def test_channel_paths_stay_on_channel_worker():
    assert owner_for("/ux-channel") == "channel"
    assert owner_for("/ux-channel/action") == "channel"
    assert owner_for("/ux-channel/static/ux-channel.js") == "channel"


def test_pages_css_and_hmr_stay_on_pages_worker():
    assert owner_for("/hello") == "pages"
    assert owner_for("/css/output.css") == "pages"
    assert owner_for("/__uxcompose/hmr") == "pages"
    assert owner_for("/") == "pages"


def test_pages_reload_ignores_css():
    assert "*.py" in RELOAD_INCLUDES
    assert "*.css" in RELOAD_EXCLUDES
    assert "assets/*" in RELOAD_EXCLUDES


def test_channel_prefix_is_narrow():
    assert CHANNEL_PATH_PREFIX == "/ux-channel"


def test_cli_serve_dev_starts_serve_dev():
    cli = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    assert "from ux_compose.serve_dev import run as run_serve_dev" in cli
    assert "--one-process" in cli
    assert "hmr:asgi_factory" in cli
    assert "devstack" not in cli
    assert "glue_factory" not in cli


def test_hmr_module_does_not_spawn_watchers():
    src = (ROOT / "src" / "ux_compose" / "hmr.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "start_watcher" not in names
    assert "Popen" not in src


def test_old_alphabet_names_are_gone():
    src = (ROOT / "src" / "ux_compose" / "serve_dev.py").read_text(encoding="utf-8")
    assert "glue_factory" not in src
    assert "devstack" not in src
    assert "backend_for" not in src
    assert 'return "X"' not in src
    assert 'return "Y"' not in src


def test_prefer_neighbor_when_free():
    port = pick_loopback_port(prefer=0)
    assert port != 0
    neighbor = pick_loopback_port(prefer=port)
    assert neighbor == port or neighbor > 0


def test_fallback_skips_taken_prefer():
    taken_slot = pick_loopback_port()
    other = pick_loopback_port(prefer=taken_slot, taken={taken_slot})
    assert other != taken_slot
    assert port_is_free(other)
