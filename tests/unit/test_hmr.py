"""Unit: Dev HMR client, inject, no in-process hub."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.hmr import CLIENT_JS, HMR_PATH, client_script_tag, inject_html


def test_hmr_path():
    assert HMR_PATH == "/__uxcompose/hmr"


def test_client_script_contains_path():
    tag = client_script_tag()
    assert "<script" in tag
    assert "data-uxcompose-hmr" in tag
    assert "WebSocket" in CLIENT_JS


def test_client_reloads_on_reconnect():
    assert "isReconnect" in CLIENT_JS
    assert "location.reload()" in CLIENT_JS
    assert "waitAlive" in CLIENT_JS
    assert "close(1000)" in CLIENT_JS
    assert 'new URL("__uxcompose/hmr", location.href)' in CLIENT_JS


def test_no_hub_or_watcher():
    src = (ROOT / "src" / "ux_compose" / "hmr.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    classes = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    assert "start_watcher" not in names
    assert "HmrHub" not in classes


def test_inject_before_last_body():
    script = b"<script data-uxcompose-hmr>X</script>"
    body = b"<html><body>hi</body></html>"
    out = inject_html(body, script)
    assert out == b"<html><body>hi<script data-uxcompose-hmr>X</script></body></html>"
    assert inject_html(out, script) == out


def test_cli_serve_does_not_xor():
    src = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    assert "needs --no-reload" not in src
    assert "hmr:asgi_factory" in src
    assert "hmr and not reload" not in src
    assert "factory=True" in src
