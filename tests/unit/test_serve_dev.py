"""origin / ui / channel routing — no live servers."""
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
    listen_loopback,
    worker_for,
)


def test_channel_paths_stay_on_channel_worker():
    assert worker_for("/ux-channel") == "channel"
    assert worker_for("/ux-channel/action") == "channel"
    assert worker_for("/ux-channel/static/ux-channel.js") == "channel"


def test_ui_keeps_routes_css_and_hmr():
    assert worker_for("/hello") == "ui"
    assert worker_for("/css/output.css") == "ui"
    assert worker_for("/__uxcompose/hmr") == "ui"
    assert worker_for("/") == "ui"


def test_ui_reload_ignores_css():
    assert "*.py" in RELOAD_INCLUDES
    assert "*.css" in RELOAD_EXCLUDES
    assert "assets/*" in RELOAD_EXCLUDES


def test_channel_prefix_is_narrow():
    assert CHANNEL_PATH_PREFIX == "/ux-channel"


def test_cli_has_no_dead_names():
    cli = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    serve = (ROOT / "src" / "ux_compose" / "serve_dev.py").read_text(encoding="utf-8")
    assert "devstack" not in cli
    assert "glue_factory" not in cli
    assert "--one-process" not in cli
    assert "hmr:asgi_factory" in serve


def test_hmr_module_does_not_spawn_watchers():
    src = (ROOT / "src" / "ux_compose" / "hmr.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert "start_watcher" not in names
    assert "Popen" not in src


def test_dead_names_are_gone():
    src = (ROOT / "src" / "ux_compose" / "serve_dev.py").read_text(encoding="utf-8")
    assert "glue_factory" not in src
    assert "devstack" not in src
    assert "backend_for" not in src
    assert "owner_for" not in src
    assert "public_asgi" not in src
    assert "PAGES_URL" not in src
    assert 'return "pages"' not in src
    assert 'return "X"' not in src
    assert 'return "Y"' not in src


def test_listen_loopback_owns_the_port():
    sock = listen_loopback()
    try:
        host, port = sock.getsockname()
        assert host == "127.0.0.1"
        assert port > 0
        other = listen_loopback()
        try:
            assert other.getsockname()[1] != port
        finally:
            other.close()
    finally:
        sock.close()


def test_workers_inherit_a_held_fd():
    src = (ROOT / "src" / "ux_compose" / "serve_dev.py").read_text(encoding="utf-8")
    assert "def listen_loopback" in src
    assert "--fd" in src
    assert "pick_loopback_port" not in src
    assert "port + 1" not in src
    assert "origin_asgi" in src
    assert "worker_for" in src
    assert "UXCOMPOSE_UI_URL" in src
