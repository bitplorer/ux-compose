"""HTMX adapter (ux_compose.htmx), ported from ux-dom 360172d (before ux-dom#140).

Sources: test_htmx_route_and_partial.py, test_htmx_ws_stream.py
(TestHtmxPureASGI, TestHtmxPrefix), test_surface_coverage.py (sse on/off),
test_parsing_chaos.py::test_htmx_details. Plus build(use_htmx=True) on both hosts.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from tests.asgi_http import asgi_http
from ux_compose.htmx import (
    HTMX_JS,
    IDIOMORPH_EXT_JS,
    SSE_EXT_JS,
    Htmx,
    HtmxDetails,
    HtmxMiddleware,
    HtmxRoutes,
)

VERBS = ("get", "post", "put", "patch", "delete")


def _body(rt: Htmx) -> str:
    return "".join(str(x) for x in rt.document_body())


# ── script runtime ────────────────────────────────────────────────────────


def test_scripts_are_pinned_with_sri():
    html = _body(Htmx())
    assert 'src="https://unpkg.com/htmx.org@2.0.4/dist/htmx.min.js"' in html
    assert (
        'integrity="sha384-HGfztofotfshcF7+8n44JQL2oJmowVChPTg48S+jvZoztPfvwD79OC/LTtG6dMp+"'
        in html
    )
    assert html.count('crossorigin="anonymous"') == 2
    assert f'src="{IDIOMORPH_EXT_JS[0]}"' in html and IDIOMORPH_EXT_JS[1] in html
    assert "1.9.2" not in html


def test_every_pinned_file_names_an_exact_version_and_sha384():
    for src, sri in (HTMX_JS, IDIOMORPH_EXT_JS, SSE_EXT_JS):
        assert src.startswith("https://unpkg.com/") and src.endswith(".min.js")
        assert "@" in src and "@latest" not in src
        assert sri.startswith("sha384-") and len(sri) == len("sha384-") + 64


def test_sse_script_included_when_enabled():
    html = _body(Htmx(sse=True))
    assert "htmx.org" in html
    assert f'src="{SSE_EXT_JS[0]}"' in html and SSE_EXT_JS[1] in html


def test_sse_off_by_default():
    assert "htmx-ext-sse" not in _body(Htmx())


def test_idiomorph_and_cdn_toggles():
    assert "idiomorph" not in _body(Htmx(idiomorph=False))
    assert Htmx(cdn=False).document_body() == []


def test_runtime_shape():
    rt = Htmx()
    assert (rt.plugin_kind, rt.name) == ("control", "htmx")
    assert rt.artifacts() == () and rt.document_head() == ()
    assert rt.wire(hx_get="/x") == {"hx_get": "/x"}


# ── partial detection ─────────────────────────────────────────────────────


def _policy(headers) -> str:
    class Req:
        pass

    req = Req()
    req.headers = headers  # type: ignore[attr-defined]
    return Htmx().partial_policy(req)


def test_hx_request_false_is_full():
    assert _policy({"HX-Request": "false"}) == "full"


def test_history_restore_is_full():
    headers = {"hx-request": "true", "hx-history-restore-request": "true"}
    assert _policy(headers) == "full"


def test_hx_request_true_is_partial():
    assert _policy({"HX-Request": "true"}) == "partial"


def test_no_headers_is_full():
    assert _policy(None) == "full"


def test_header_dict_with_type_key_is_not_a_scope():
    assert _policy({"type": "x", "HX-Request": "true"}) == "partial"


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"HX-Request": "true"}, True),
        ({"hx-request": "true"}, True),
        ({"HX-Request": "True"}, False),
        ({"HX-Request": True}, False),
        ({"HX-Request": "1"}, False),
        ({"HX-Request": "false"}, False),
        ({}, False),
        ({"HX-Request": "true", "HX-History-Restore-Request": "true"}, False),
        ({"HX-Request": "true", "HX-History-Restore-Request": "false"}, True),
    ],
)
def test_details_partial_values(headers, expected):
    assert HtmxDetails(headers).partial is expected


def test_htmx_details():
    d = HtmxDetails(
        {"HX-Request": "true", "HX-Target": "main", "HX-Triggering-Event": '{"a":1}'}
    )
    assert d
    assert d.target == "main"
    assert d.triggering_event == {"a": 1}
    assert HtmxDetails({"HX-Triggering-Event": "not-json"}).triggering_event is None


def test_uri_autoencoded_header_is_unquoted():
    d = HtmxDetails({"HX-Prompt": "a%20b", "HX-Prompt-URI-AutoEncoded": "true"})
    assert d.prompt == "a b"


def test_details_from_scope():
    scope = {
        "type": "http",
        "headers": [(b"hx-request", b"true"), (b"hx-trigger", b"btn")],
    }
    d = HtmxDetails(scope)
    assert bool(d)
    assert d.trigger == "btn"


# ── middleware ────────────────────────────────────────────────────────────


def test_middleware_sets_request_state():
    app = FastAPI()
    app.add_middleware(HtmxMiddleware)

    @app.get("/ping")
    def ping(request: Request):
        h = request.state.htmx
        return {"is_htmx": bool(h), "target": h.target}

    client = TestClient(app)
    assert client.get("/ping").json()["is_htmx"] is False
    r = client.get("/ping", headers={"HX-Request": "true", "HX-Target": "main"})
    assert r.json() == {"is_htmx": True, "target": "main"}


def test_streaming_still_works_with_middleware():
    """BaseHTTPMiddleware broke streaming; pure ASGI must not."""
    from ux_dom.dom import div
    from ux_dom.response.starlette import StreamingResponse

    app = FastAPI()
    app.add_middleware(HtmxMiddleware)

    @app.get("/stream2")
    def stream2():
        return StreamingResponse(div("stream-body"))

    r = TestClient(app).get("/stream2")
    assert r.status_code == 200
    assert "stream-body" in r.text


def test_mount_adds_middleware_only_when_asked():
    class Host:
        def __init__(self):
            self.added = []

        def add_middleware(self, cls):
            self.added.append(cls)

    off, on = Host(), Host()
    Htmx().mount(off)
    Htmx(middleware=True).mount(on)
    assert off.added == [] and on.added == [HtmxMiddleware]


# ── routes ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize("verb", VERBS)
def test_string_form_routes_the_decorated_function(verb):
    app = FastAPI()
    h = HtmxRoutes(api=app, prefix="/a")

    @getattr(h, verb)("named")
    def handler():
        return {"ok": verb}

    assert handler.__name__ == "handler"
    r = TestClient(app).request(verb.upper(), "/a/named")
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": verb}


def test_prefix_paths():
    class API:
        def __init__(self):
            self.routes = []

        def _reg(self, method):
            def deco_path(path):
                def deco(fn):
                    self.routes.append((method, path))
                    return fn

                return deco

            return deco_path

        def get(self, path):
            return self._reg("GET")(path)

        def post(self, path):
            return self._reg("POST")(path)

    api = API()

    @HtmxRoutes(api, prefix="/actions/").get
    def counter():
        pass

    api2 = API()

    @HtmxRoutes(api2).post
    def save():
        pass

    assert api.routes == [("GET", "/actions/counter")]
    assert api2.routes == [("POST", "/save")]


# ── build(use_htmx=True): full page vs partial, both hosts ───────────────


@pytest.mark.parametrize("host", ["fastapi", "asgi"])
def test_build_use_htmx_full_page_and_partial(tmp_path, host):
    from ux_dom import Csp, Document, XElement

    from ux_compose.build import build
    from ux_compose.scaffold import create_app

    root = create_app(tmp_path / f"hx_{host}", name="hx", level=1, host=host)
    doc = Document(head=[], body=[], ensure_csrf_token=False)
    doc.use(XElement(), Csp.auto())
    _, asgi, _ = build(
        root, name="hx", host=host, live="null", level=1, document=doc, use_htmx=True
    )

    def get(headers=None) -> str:
        status, _, body = asgi_http(asgi, "/hello", headers=headers)
        assert status == 200
        return body.decode()

    full = get()
    assert "<html" in full and HTMX_JS[0] in full and HTMX_JS[1] in full
    restore = get({"HX-Request": "true", "HX-History-Restore-Request": "true"})
    assert "<html" in restore and HTMX_JS[0] in restore
    part = get({"HX-Request": "true"})
    assert 'id="hello"' in part
    assert "<html" not in part and "htmx.org" not in part


def test_build_without_htmx_wraps_hx_request(tmp_path):
    from ux_dom import Document

    from ux_compose.build import build
    from ux_compose.scaffold import create_app

    root = create_app(tmp_path / "plain", name="plain", level=1, host="asgi")
    doc = Document(head=[], body=[], ensure_csrf_token=False)
    _, asgi, _ = build(root, name="plain", host="asgi", live="null", level=1, document=doc)
    _, _, body = asgi_http(asgi, "/hello", headers={"HX-Request": "true"})
    assert b"<html" in body and b"htmx.org" not in body
