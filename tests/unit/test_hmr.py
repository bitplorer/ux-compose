"""Unit: Dev HMR client, HTML insert, no in-process hub."""
from __future__ import annotations

import ast
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.hmr import (
    CLIENT_JS,
    HMR_PATH,
    HmrClientMiddleware,
    client_script_tag,
    insert_hmr_client,
    load_asgi,
)


def test_hmr_path():
    assert HMR_PATH == "/__uxcompose/hmr"


def test_client_script_contains_path():
    tag = client_script_tag()
    assert "<script" in tag
    assert "data-uxcompose-hmr" in tag
    assert "WebSocket" in CLIENT_JS


def test_client_morphs_on_reconnect():
    assert "function softReload" in CLIENT_JS
    assert "function morphLive" in CLIENT_JS
    assert "function hardReload" in CLIENT_JS
    assert "waitUntilWorkerServes(softReload)" in CLIENT_JS
    assert "location.reload()" in CLIENT_JS
    assert "DOMParser" in CLIENT_JS
    assert "Idiomorph" in CLIENT_JS
    assert "hmr-no-target" in CLIENT_JS
    assert "close(1000)" in CLIENT_JS
    assert 'new URL("__uxcompose/hmr", location.href)' in CLIENT_JS
    assert "reloadPage" not in CLIENT_JS


def test_client_keeps_polling_and_shows_wait_banner():
    assert "function showFail" in CLIENT_JS
    assert "function hideFail" in CLIENT_JS
    assert "waiting for ui worker" in CLIENT_JS
    assert "uxcompose-hmr-fail" in CLIENT_JS
    assert "if (n > 80) return;" not in CLIENT_JS


def test_client_restores_focus_and_scroll():
    assert "function snapshotUi" in CLIENT_JS
    assert "function restoreUi" in CLIENT_JS
    assert "selectionStart" in CLIENT_JS
    assert "setSelectionRange" in CLIENT_JS
    assert "scrollTo" in CLIENT_JS
    assert "restoreUi(snap)" in CLIENT_JS
    assert 'getAttribute("name")' in CLIENT_JS
    assert "[name=" in CLIENT_JS


def test_client_polls_css_and_swaps_sheet():
    assert "function watchCss" in CLIENT_JS
    assert "function swapStylesheets" in CLIENT_JS
    assert 'method: "HEAD"' in CLIENT_JS
    assert "/css/output.css" in CLIENT_JS
    assert "watchCss();" in CLIENT_JS


def test_no_hub_or_watcher():
    src = (ROOT / "src" / "ux_compose" / "hmr.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    classes = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    assert "start_watcher" not in names
    assert "inject_html" not in names
    assert "HmrHub" not in classes


def test_insert_hmr_client_before_last_body():
    script = b"<script data-uxcompose-hmr>X</script>"
    page = b"<html><body>hi</body></html>"
    out = insert_hmr_client(page, script)
    assert out == b"<html><body>hi<script data-uxcompose-hmr>X</script></body></html>"
    assert insert_hmr_client(out, script) == out


def test_insert_hmr_client_skips_without_body():
    script = b"<script data-uxcompose-hmr>X</script>"
    page = b"<html>no close"
    assert insert_hmr_client(page, script) == page


def test_cli_serve_does_not_xor():
    src = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    serve = (ROOT / "src" / "ux_compose" / "serve_dev.py").read_text(encoding="utf-8")
    assert "needs --no-reload" not in src
    assert "hmr and not reload" not in src
    assert "run_serve_dev" in src
    assert "--one-process" not in src
    assert "hmr:asgi_factory" in serve


def test_cli_css_watch_is_sibling_not_hmr_watcher():
    cli = (ROOT / "src" / "ux_compose" / "cli.py").read_text(encoding="utf-8")
    hmr = (ROOT / "src" / "ux_compose" / "hmr.py").read_text(encoding="utf-8")
    assert "def _start_tailwind_watch" in cli
    assert "argv_with_io" in cli
    assert "Popen" in cli
    assert "Popen" not in hmr
    assert "subprocess" not in hmr
    assert "discover_css_io" not in hmr


def test_docs_do_not_teach_css_mtime_hmr():
    tw = (ROOT / "docs" / "guides" / "TAILWIND.md").read_text(encoding="utf-8")
    assert "watches `.css`" not in tw
    assert "reloads on `.css` mtime" not in tw
    cli = (ROOT / "docs" / "guides" / "CLI.md").read_text(encoding="utf-8")
    assert "watches `.css`" not in cli


def test_agents_lock_three_clocks():
    """Stop the next agent collapsing clocks back into a hub + watcher."""
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    flow = (ROOT / "docs" / "FLOW.md").read_text(encoding="utf-8")
    assert "Dev clocks under `uxcompose serve`" in agents
    assert "HmrHub" in agents
    assert "sibling Tailwind" in agents
    assert "Popen` inside `hmr.py" in flow
    assert "CSS sibling --watch" in flow


def test_load_asgi_requires_module_attr():
    try:
        load_asgi("not-a-spec")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "module:attr" in str(exc)


def _run_asgi(app, *, path="/", method="GET", content_type: bytes, body: bytes, extra_headers=None):
    captured = []

    async def inner(scope, receive, send):
        headers = [(b"content-type", content_type), (b"content-length", str(len(body)).encode())]
        if extra_headers:
            headers.extend(extra_headers)
        await send({"type": "http.response.start", "status": 200, "headers": headers})
        await send({"type": "http.response.body", "body": body, "more_body": False})

    async def send(msg):
        captured.append(msg)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    mw = HmrClientMiddleware(inner, client_script_tag())
    asyncio.run(mw({"type": "http", "path": path, "method": method, "headers": []}, receive, send))
    return captured


def test_middleware_injects_html_and_drops_length():
    page = b"<html><body>hi</body></html>"
    captured = _run_asgi(None, content_type=b"text/html; charset=utf-8", body=page)
    start = next(m for m in captured if m["type"] == "http.response.start")
    body = next(m for m in captured if m["type"] == "http.response.body")
    headers = dict(start["headers"])
    assert b"content-length" not in headers
    assert b"data-uxcompose-hmr" in body["body"]
    assert body["body"].endswith(b"</body></html>")


def test_middleware_keeps_length_on_non_html():
    captured = _run_asgi(
        None,
        content_type=b"text/css; charset=utf-8",
        body=b"body{color:red}",
        extra_headers=[(b"last-modified", b"Wed, 01 Jan 2020 00:00:00 GMT")],
    )
    start = next(m for m in captured if m["type"] == "http.response.start")
    body = next(m for m in captured if m["type"] == "http.response.body")
    headers = dict(start["headers"])
    assert headers.get(b"content-length") == b"15"
    assert headers.get(b"last-modified") == b"Wed, 01 Jan 2020 00:00:00 GMT"
    assert body["body"] == b"body{color:red}"
    assert b"data-uxcompose-hmr" not in body["body"]


def test_start_tailwind_watch_none_without_input(tmp_path):
    from ux_compose.cli import _start_tailwind_watch

    assert _start_tailwind_watch(cwd=str(tmp_path)) is None
