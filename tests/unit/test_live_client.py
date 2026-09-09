"""Fragment Cap live-client: public URL refs, no Cap re-impl, no Document wrap."""
from __future__ import annotations

import ast
import asyncio
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.algebra import bind, control
from ux_compose.live_client import (
    CHANNEL_BRIDGE_URL,
    CHANNEL_ENDPOINT,
    CHANNEL_JS_URL,
    LiveClientMiddleware,
    attach_live_client,
    insert_live_client,
    live_client_script_tags,
)
from ux_compose.scaffold import DOCUMENT_PY

from tests.asgi_http import asgi_get

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None


def _pkg(tmp_path: Path, files: dict[str, str], name: str = "fraglive") -> Path:
    """Unique package name — DirectoryRoutes caches modules in sys.modules."""
    pkg = tmp_path / name
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    for rel, src in files.items():
        dest = pkg / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(src, encoding="utf-8")
    return pkg


def test_public_url_pins():
    assert CHANNEL_JS_URL == "/ux-channel/static/ux-channel.js"
    assert CHANNEL_BRIDGE_URL == "/ux-channel/static/ux-bridge.js"
    assert CHANNEL_ENDPOINT == "/ux-channel/action"
    tags = live_client_script_tags()
    assert CHANNEL_JS_URL in tags
    assert "<script" in tags
    assert "data-uxcompose-live-client" in tags


def test_live_client_source_does_not_import_ux_channel():
    src = (ROOT / "src" / "ux_compose" / "live_client.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("ux_channel")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            assert not mod.startswith("ux_channel")


def test_control_emits_dual_action_attrs():
    attrs = control("hello.inc", sku="tee")
    assert attrs["data-ux-action"] == "hello.inc"
    assert attrs["data-channel-action"] == "hello.inc"
    assert attrs["data-ux-arg-sku"] == "tee"
    assert "data-channel-args" in attrs
    assert "tee" in attrs["data-channel-args"]


def test_bind_string_fallback_emits_dual_attrs():
    attrs = bind("cart.add", sku="oak")
    assert attrs["data-ux-action"] == "cart.add"
    assert attrs["data-channel-action"] == "cart.add"
    assert attrs["data-ux-arg-sku"] == "oak"


def test_insert_live_client_wraps_fragment_not_document():
    page = b'<div id="hello">hi</div>'
    out = insert_live_client(page)
    text = out.decode("utf-8")
    assert '<div id="hello">hi</div>' in text
    assert CHANNEL_JS_URL in text
    assert f'data-channel-endpoint="{CHANNEL_ENDPOINT}"' in text
    assert "data-uxcompose-live-client" in text
    assert insert_live_client(out) == out  # idempotent


def test_insert_live_client_does_not_double_wrap_complete_document():
    page = (
        b"<!DOCTYPE html><html><body>"
        b'<div id="hello">hi</div>'
        b"</body></html>"
    )
    out = insert_live_client(page)
    text = out.decode("utf-8").lower()
    assert text.count("<html") == 1
    assert text.count("<body") == 1
    assert CHANNEL_JS_URL in out.decode("utf-8")
    assert f'data-channel-endpoint="{CHANNEL_ENDPOINT}"' in out.decode("utf-8")
    assert out.lower().index(b"<script") < out.lower().rfind(b"</body>")
    assert insert_live_client(out) == out


def test_insert_live_client_skips_when_channel_script_already_present():
    page = (
        b"<html><body>"
        b'<script src="/ux-channel/static/ux-channel.js"></script>'
        b"</body></html>"
    )
    assert insert_live_client(page) == page


def _run_asgi(app, *, path="/", content_type: bytes, body: bytes):
    captured = []

    async def inner(scope, receive, send):
        headers = [
            (b"content-type", content_type),
            (b"content-length", str(len(body)).encode()),
        ]
        await send({"type": "http.response.start", "status": 200, "headers": headers})
        await send({"type": "http.response.body", "body": body, "more_body": False})

    async def send(msg):
        captured.append(msg)

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    mw = LiveClientMiddleware(inner)
    asyncio.run(mw({"type": "http", "path": path, "method": "GET", "headers": []}, receive, send))
    return captured


def test_middleware_injects_html_and_skips_css():
    page = b'<div id="hello">hi</div>'
    captured = _run_asgi(None, content_type=b"text/html; charset=utf-8", body=page)
    body = next(m for m in captured if m["type"] == "http.response.body")
    assert CHANNEL_JS_URL.encode() in body["body"]
    start = next(m for m in captured if m["type"] == "http.response.start")
    headers = dict(start["headers"])
    assert b"content-length" not in headers

    css = b"body{color:red}"
    captured = _run_asgi(None, path="/css/output.css", content_type=b"text/css", body=css)
    body = next(m for m in captured if m["type"] == "http.response.body")
    start = next(m for m in captured if m["type"] == "http.response.start")
    headers = dict(start["headers"])
    assert body["body"] == css
    assert CHANNEL_JS_URL.encode() not in body["body"]
    assert b"content-length" in headers


def test_scaffold_document_uses_dom_channel_optional():
    assert "from ux_dom.runtime import" in DOCUMENT_PY
    assert "Channel.optional()" in DOCUMENT_PY
    assert "XElement()" in DOCUMENT_PY
    assert "Csp.auto()" in DOCUMENT_PY
    assert "from ux_channel" not in DOCUMENT_PY
    assert "import ux_channel" not in DOCUMENT_PY
    assert "document = None" not in DOCUMENT_PY
    assert "except Exception" not in DOCUMENT_PY


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi required")
def test_build_document_none_does_not_attach_live_client(tmp_path: Path):
    """Document-absent GET is not the product path; do not inject live-client."""
    pytest.importorskip("ux_channel")
    from ux_compose.build import build

    pkg = _pkg(
        tmp_path,
        {
            "routes/hello.py": (
                "from ux_compose import Component, MorphState, action, control, update_with\n"
                "class Hello(Component):\n"
                "    id = 'hello'\n"
                "    n = MorphState(0)\n"
                "    def render(self):\n"
                "        attrs = control('hello.inc')\n"
                "        n = int(self.n or 0)\n"
                "        return '<div id=\"hello\">%s<button %s>+1</button></div>' % (\n"
                "            n, ' '.join(f'{k}=\"{v}\"' for k, v in attrs.items())\n"
                "        )\n"
                "    @action(caps=())\n"
                "    def inc(self):\n"
                "        self.n = int(self.n or 0) + 1\n"
                "        return update_with(self)\n"
            )
        },
        name="frag_inject",
    )
    app, asgi, _bundle = build(
        pkg, name="Demo", host="fastapi", live="auto", level=1, document=None
    )
    if getattr(app, "_channel", None) is None:
        pytest.skip("Channel did not attach")
    r = asgi_get(asgi, "/hello")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")
    assert "data-uxcompose-live-client" not in r.text
    assert 'data-ux-action="hello.inc"' in r.text
    assert hasattr(asgi, "mount")


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi required")
def test_build_live_null_fragment_has_no_channel_client(tmp_path: Path):
    from ux_compose.build import build

    pkg = _pkg(
        tmp_path,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    def render(self):\n"
                "        return '<div id=\"hello\">hi</div>'\n"
            )
        },
        name="frag_null",
    )
    app, asgi, _bundle = build(
        pkg, name="Demo", host="fastapi", live="null", level=1, document=None
    )
    assert getattr(app, "_channel", None) is None
    r = asgi_get(asgi, "/hello")
    assert r.status_code == 200
    assert "hello" in r.text
    assert CHANNEL_JS_URL not in r.text
    assert "data-channel-endpoint" not in r.text
    assert r.text.count("<html") <= 1


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi required")
def test_build_author_document_is_not_double_wrapped(tmp_path: Path):
    pytest.importorskip("ux_channel")
    from ux_compose.build import build

    pkg = _pkg(
        tmp_path,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    def render(self):\n"
                "        return '<div id=\"hello\">hi</div>'\n"
            )
        },
        name="frag_author",
    )

    def document(child=None):
        return (
            "<!DOCTYPE html><html><body data-channel-endpoint="
            f'"{CHANNEL_ENDPOINT}">AUTHOR{child}'
            f'<script src="{CHANNEL_JS_URL}"></script></body></html>'
        )

    app, asgi, _bundle = build(
        pkg, name="Demo", host="fastapi", live="auto", level=1, document=document
    )
    if getattr(app, "_channel", None) is None:
        pytest.skip("Channel did not attach")
    r = asgi_get(asgi, "/hello")
    assert r.status_code == 200
    assert "AUTHOR" in r.text
    assert "hello" in r.text
    assert r.text.lower().count("<html") == 1
    assert r.text.count(CHANNEL_JS_URL) == 1


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi required")
def test_complete_document_fragment_path_is_not_double_wrapped(tmp_path: Path):
    pytest.importorskip("ux_channel")
    from ux_compose.build import build

    pkg = _pkg(
        tmp_path,
        {
            "routes/hello.py": (
                "class Hello:\n"
                "    def render(self):\n"
                "        return ("
                "'<!DOCTYPE html><html><body>"
                "<div id=\"hello\">hi</div>"
                "</body></html>'\n"
                "        )\n"
            )
        },
        name="frag_complete",
    )
    app, asgi, _bundle = build(
        pkg, name="Demo", host="fastapi", live="auto", level=1, document=None
    )
    if getattr(app, "_channel", None) is None:
        pytest.skip("Channel did not attach")
    r = asgi_get(asgi, "/hello")
    assert r.status_code == 200
    assert r.text.lower().count("<html") == 1
    assert r.text.lower().count("<body") == 1
    assert "data-uxcompose-live-client" not in r.text
    assert "hello" in r.text


def test_attach_live_client_is_idempotent():
    inner = object()

    class _App:
        def __init__(self):
            self.app = inner
            self.n = 0

        def add_middleware(self, cls, **kwargs):
            self.n += 1
            self.app = cls(self.app, **kwargs)

    app = _App()
    out = attach_live_client(app)
    out2 = attach_live_client(out)
    assert out is app
    assert out2 is app
    assert app.n == 1
