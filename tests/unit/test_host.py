"""Product FastAPI host — Clock A fitness function."""
from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ux_compose.routing.core import DirectoryRoutes, http_path, is_json_payload, is_stream_payload


def test_is_json_payload():
    assert is_json_payload({"ok": True})
    assert is_json_payload([{"a": 1}])
    assert is_json_payload([])
    assert not is_json_payload("<div>hi</div>")
    assert not is_json_payload(b"<div>")
    assert not is_json_payload(None)


def test_is_stream_payload():
    def gen():
        yield "a"
        yield "b"

    assert is_stream_payload(gen())
    assert not is_stream_payload("<div>hi</div>")
    assert not is_stream_payload({"ok": True})
    assert not is_stream_payload([{"a": 1}])
    assert not is_stream_payload(None)


def test_http_path_law():
    assert http_path("hello") == "/hello"
    assert http_path("index") == "/"
    assert http_path("route") == "/"
    assert http_path("shop", "index") == "/shop"
    assert http_path("shop", "[sku]") == "/shop/{sku}"
    assert http_path("[id]", "page") == "/{id}/page"


def test_discover_index_and_param(tmp_path: Path):
    pkg = tmp_path / "shop"
    routes = pkg / "routes"
    (routes / "shop").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "index.py").write_text(
        "class Index:\n    def render(self):\n        return 'home'\n",
        encoding="utf-8",
    )
    (routes / "shop" / "[sku].py").write_text(
        "class Sku:\n    def render(self, sku='x'):\n        return sku\n",
        encoding="utf-8",
    )
    core = DirectoryRoutes(pkg, base_directory="routes")
    recs = core.discover()
    paths = {r.path for r in recs}
    assert "/" in paths
    assert "/shop/{sku}" in paths
    assert all(r.kind == "page" and r.method == "GET" for r in recs)


def test_build_fastapi_page_is_html(tmp_path: Path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")

    pkg = tmp_path / "demo"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(
        "class Hello:\n"
        "    id = 'hello'\n"
        "    def render(self):\n"
        "        return '<div id=\"hello\">hi</div>'\n",
        encoding="utf-8",
    )
    from ux_compose.build import build

    _app, asgi, bundle = build(pkg, name="Demo", host="fastapi", live="null", level=1)
    assert bundle is not None
    paths = [r.get("path") for r in (bundle.route_table or [])]
    assert "/hello" in paths

    from fastapi.testclient import TestClient

    client = TestClient(asgi)
    r = client.get("/hello")
    assert r.status_code == 200
    ctype = r.headers.get("content-type", "")
    assert "text/html" in ctype
    assert "hello" in r.text
    assert r.headers.get("content-length") is not None


def test_build_param_route(tmp_path: Path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")

    pkg = tmp_path / "shop"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "[sku].py").write_text(
        "class Sku:\n"
        "    def render(self, sku='x'):\n"
        "        return f'<div id=\"sku\">{sku}</div>'\n",
        encoding="utf-8",
    )
    from ux_compose.build import build
    from fastapi.testclient import TestClient

    _app, asgi, _bundle = build(pkg, name="Shop", host="fastapi", live="null", level=1)
    r = TestClient(asgi).get("/oak")
    assert r.status_code == 200
    assert "oak" in r.text
    assert "text/html" in r.headers.get("content-type", "")


def test_build_json_route_untouched(tmp_path: Path):
    pytest.importorskip("fastapi")
    pkg = tmp_path / "demo"
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "routes" / "hello.py").write_text(
        "class Hello:\n    def render(self):\n        return 'x'\n",
        encoding="utf-8",
    )
    from ux_compose.build import build

    _app, asgi, _bundle = build(pkg, name="Demo", host="fastapi", live="null", level=1)

    @asgi.get("/api/health")
    def health():
        return {"ok": True}

    from fastapi.testclient import TestClient

    r = TestClient(asgi).get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_page_render_dict_is_json(tmp_path: Path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")

    pkg = tmp_path / "demo"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "health.py").write_text(
        "class Health:\n"
        "    def render(self):\n"
        "        return {'ok': True, 'n': 1}\n",
        encoding="utf-8",
    )
    from ux_compose.build import build
    from fastapi.testclient import TestClient

    _app, asgi, _bundle = build(pkg, name="Demo", host="fastapi", live="null", level=1)
    r = TestClient(asgi).get("/health")
    assert r.status_code == 200
    assert "json" in r.headers.get("content-type", "")
    assert r.json() == {"ok": True, "n": 1}


def test_page_render_generator_streams(tmp_path: Path):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")

    pkg = tmp_path / "demo"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "ticks.py").write_text(
        "class Ticks:\n"
        "    def render(self):\n"
        "        def gen():\n"
        "            yield '<div>a</div>'\n"
        "            yield '<div>b</div>'\n"
        "        return gen()\n",
        encoding="utf-8",
    )
    from ux_compose.build import build
    from ux_compose.routing.fastapi import _as_http_response
    from fastapi.testclient import TestClient

    def gen():
        yield "<div>a</div>"
        yield "<div>b</div>"

    wrapped = _as_http_response(gen())
    assert "Streaming" in type(wrapped).__name__

    _app, asgi, _bundle = build(pkg, name="Demo", host="fastapi", live="null", level=1)
    r = TestClient(asgi).get("/ticks")
    assert r.status_code == 200
    assert "a" in r.text and "b" in r.text
    assert "html" in r.headers.get("content-type", "")


def test_build_asgi_degrade(tmp_path: Path):
    pkg = tmp_path / "demo"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(
        "class Hello:\n"
        "    def render(self):\n"
        "        return '<div id=\"hello\">hi</div>'\n",
        encoding="utf-8",
    )
    from ux_compose.build import build
    from ux_compose.routing.asgi import DirectoryASGI

    _app, asgi, bundle = build(pkg, name="Demo", host="asgi", live="null", level=1)
    assert isinstance(asgi, DirectoryASGI)
    paths = [r.get("path") for r in (bundle.route_table or [])]
    assert "/hello" in paths

    status = {}
    body = b""

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(msg):
        nonlocal body
        if msg["type"] == "http.response.start":
            status["code"] = msg["status"]
            status["headers"] = dict(msg.get("headers") or [])
        elif msg["type"] == "http.response.body":
            body += msg.get("body") or b""

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/hello",
        "query_string": b"",
        "headers": [],
    }
    asyncio.run(asgi(scope, receive, send))
    assert status.get("code") == 200
    assert b"hello" in body
    ctype = status.get("headers", {}).get(b"content-type", b"").decode()
    assert "text/html" in ctype


def test_build_batteries_fails_closed(tmp_path: Path):
    from ux_compose.build import build
    from ux_compose.routing.host import ProductBatteriesRejected

    pkg = tmp_path / "demo"
    (pkg / "routes").mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    with pytest.raises(ProductBatteriesRejected):
        build(pkg, name="Demo", host="batteries")


def test_host_fastapi_missing_fails_closed(monkeypatch):
    from ux_compose.routing import host as hostmod

    def _boom(*_a, **_k):
        raise ImportError("fastapi missing")

    monkeypatch.setattr("ux_compose.routing.fastapi.create", _boom)
    with pytest.raises(ImportError):
        hostmod.open(name="T", host="fastapi")


def test_boot_auto_is_l1():
    from ux_compose import App

    app = App.boot("T")
    assert int(app.level) == 1


def test_adapters_shim_still_imports():
    from ux_compose.routing.adapters.fastapi import materialize, mount
    from ux_compose.routing.adapters.asgi import DirectoryASGI

    assert callable(materialize) and callable(mount)
    assert DirectoryASGI is not None
