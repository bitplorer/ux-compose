"""Locks for silent failures that have one obvious correction."""
from __future__ import annotations

import logging
import sqlite3
import sys
import types
from pathlib import Path

import pytest

from ux_compose.routing import DirectoryRoutes, DirectoryRoutesError, RouterHooks
from ux_compose.routing.asgi import DirectoryASGI, match_record
from ux_compose.routing.core import RouteRecord, pick_page_type
from ux_compose.routing.fastapi import _live_instance

ROOT = Path(__file__).resolve().parents[2]


def _purge_modules(prefix: str) -> None:
    for key in list(sys.modules):
        if key == prefix or key.startswith(prefix + "."):
            sys.modules.pop(key, None)


def test_fail_closed_reraises_route_import_error(tmp_path: Path):
    pkg = tmp_path / "shopfail"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(
        "class Hello:\n    def render(self):\n        return 'ok'\n",
        encoding="utf-8",
    )
    (routes / "boom.py").write_text("raise RuntimeError('boom-import')\n", encoding="utf-8")
    _purge_modules("shopfail")
    try:
        core = DirectoryRoutes(pkg, fail_closed=True)
        with pytest.raises(RuntimeError, match="boom-import"):
            core.discover()
    finally:
        _purge_modules("shopfail")


def test_fail_closed_import_error_is_raised_again_on_the_next_discover(tmp_path: Path):
    pkg = tmp_path / "shopsticky"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(
        "class Hello:\n    def render(self):\n        return 'ok'\n",
        encoding="utf-8",
    )
    (routes / "boom.py").write_text("raise RuntimeError('boom-import')\n", encoding="utf-8")
    _purge_modules("shopsticky")
    try:
        core = DirectoryRoutes(pkg, fail_closed=True)
        with pytest.raises(RuntimeError, match="boom-import"):
            core.discover()
        with pytest.raises(RuntimeError, match="boom-import"):
            core.discover()
    finally:
        _purge_modules("shopsticky")


def test_fail_open_still_skips_a_bad_route_import(tmp_path: Path):
    """Characterization: this passed on #102 before the fail-closed fix."""
    pkg = tmp_path / "shopopen"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(
        "class Hello:\n    def render(self):\n        return 'ok'\n",
        encoding="utf-8",
    )
    (routes / "boom.py").write_text("raise RuntimeError('boom-import')\n", encoding="utf-8")
    _purge_modules("shopopen")
    try:
        core = DirectoryRoutes(pkg, fail_closed=False)
        recs = core.discover()
    finally:
        _purge_modules("shopopen")
    assert {r.path for r in recs} == {"/hello"}


def test_accept_symbol_raise_propagates_when_fail_closed():
    mod = types.ModuleType("demo.routes.hello")

    class Hello:
        def render(self):
            return "hi"

    Hello.__module__ = mod.__name__
    mod.Hello = Hello

    def boom(name, obj, module):
        raise RuntimeError("hook-broke")

    with pytest.raises(RuntimeError, match="hook-broke"):
        pick_page_type(
            mod,
            ["Hello"],
            "hello",
            accept_symbol=boom,
            fail_closed=True,
        )


def test_accept_symbol_raise_skips_when_not_fail_closed():
    """Characterization: this passed on #102 before the fail-closed fix."""
    mod = types.ModuleType("demo.routes.hello2")

    class Hello:
        def render(self):
            return "hi"

    Hello.__module__ = mod.__name__
    mod.Hello = Hello

    def boom(name, obj, module):
        raise RuntimeError("hook-broke")

    assert (
        pick_page_type(
            mod,
            ["Hello"],
            "hello",
            accept_symbol=boom,
            fail_closed=False,
        )
        is None
    )


def test_resolve_unit_error_is_not_replaced_with_a_new_instance():
    class Page:
        def __init__(self):
            self.n = 0

        def render(self):
            return str(self.n)

    rec = RouteRecord(method="GET", path="/hello", name="Page", page_cls=Page)

    def resolve(cls, path, name):
        raise RuntimeError("resolve-broke")

    with pytest.raises(RuntimeError, match="resolve-broke"):
        _live_instance(rec, resolve, {})


def test_directory_asgi_resolve_error_is_http_500(tmp_path: Path, caplog):
    from tests.asgi_http import asgi_http

    class Page:
        def __init__(self):
            self.n = 0

        def render(self):
            return "<div>0</div>"

    def resolve(cls, path, name):
        raise RuntimeError("resolve-broke")

    core = DirectoryRoutes(tmp_path, hooks=RouterHooks(resolve_unit=resolve))
    core.records = [
        RouteRecord(method="GET", path="/hello", name="Page", page_cls=Page, kind="page")
    ]
    with caplog.at_level(logging.ERROR):
        status, _headers, body = asgi_http(DirectoryASGI(core), "/hello")
    assert status == 500
    assert body == b"Internal Server Error"
    assert b"resolve-broke" not in body
    assert "resolve-broke" in caplog.text


def test_directory_asgi_constructor_error_is_http_500(tmp_path: Path, caplog):
    from tests.asgi_http import asgi_http

    class Boom:
        def __init__(self):
            raise RuntimeError("ctor-broke")

        def render(self):
            return "x"

    core = DirectoryRoutes(tmp_path)
    core.records = [
        RouteRecord(method="GET", path="/hello", name="Boom", page_cls=Boom, kind="page")
    ]
    with caplog.at_level(logging.ERROR):
        status, _headers, body = asgi_http(DirectoryASGI(core), "/hello")
    assert status == 500
    assert body == b"Internal Server Error"
    assert b"ctor-broke" not in body
    assert "ctor-broke" in caplog.text


def test_resolve_none_still_constructs_the_page(tmp_path: Path):
    """Characterization: this passed on #102 before the resolve_unit fix."""
    from tests.asgi_http import asgi_http

    class Page:
        def render(self):
            return "from-cls"

    def resolve(cls, path, name):
        return None

    core = DirectoryRoutes(tmp_path, hooks=RouterHooks(resolve_unit=resolve))
    core.records = [
        RouteRecord(method="GET", path="/hello", name="Page", page_cls=Page, kind="page")
    ]
    status, _headers, body = asgi_http(DirectoryASGI(core), "/hello")
    assert status == 200
    assert b"from-cls" in body


def test_hyphenated_param_fails_at_discover(tmp_path: Path):
    pkg = tmp_path / "itemshop"
    routes = pkg / "routes" / "item"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes.parent / "__init__.py").write_text("", encoding="utf-8")
    (routes / "[user-id].py").write_text(
        "class UserId:\n    def render(self):\n        return 'x'\n",
        encoding="utf-8",
    )
    (routes / "hello.py").write_text(
        "class Hello:\n    def render(self):\n        return 'hi'\n",
        encoding="utf-8",
    )
    _purge_modules("itemshop")
    try:
        core = DirectoryRoutes(pkg, fail_closed=True)
        with pytest.raises(DirectoryRoutesError, match="user-id"):
            core.discover()
    finally:
        _purge_modules("itemshop")


def test_identifier_param_still_matches():
    """Characterization: this passed on #102 before the path-parameter fix."""
    rec = RouteRecord(method="GET", path="/shop/{sku}", name="Sku", page_cls=object)
    hit = match_record([rec], "GET", "/shop/oak")
    assert hit is not None
    assert hit[1]["sku"] == "oak"


def test_bad_param_does_not_sink_a_later_route():
    bad = RouteRecord(method="GET", path="/item/{user-id}", name="UserId", page_cls=object)
    good = RouteRecord(method="GET", path="/hello", name="Hello", page_cls=object)
    hit = match_record([bad, good], "GET", "/hello")
    assert hit is not None
    assert hit[0].path == "/hello"
    assert match_record([bad], "GET", "/item/abc") is None


def test_directory_asgi_rejects_bad_param_at_init(tmp_path: Path):
    class Hello:
        def render(self):
            return "hi"

    core = DirectoryRoutes(tmp_path)
    core.records = [
        RouteRecord(
            method="GET",
            path="/item/{user-id}",
            name="Hello",
            page_cls=Hello,
            kind="page",
        )
    ]
    with pytest.raises(DirectoryRoutesError, match="user-id"):
        DirectoryASGI(core)


def test_head_omits_the_body(tmp_path: Path):
    from tests.asgi_http import asgi_http

    class Hello:
        def render(self):
            return "<div id='hello'>hi</div>"

    core = DirectoryRoutes(tmp_path)
    core.records = [
        RouteRecord(method="GET", path="/hello", name="Hello", page_cls=Hello, kind="page")
    ]
    app = DirectoryASGI(core)
    get_status, get_headers, get_body = asgi_http(app, "/hello", method="GET")
    head_status, head_headers, head_body = asgi_http(app, "/hello", method="HEAD")
    assert get_status == 200
    assert get_body
    assert head_status == 200
    assert head_body == b""
    assert head_headers["content-length"] == str(len(get_body))
    assert head_headers["content-type"] == get_headers["content-type"]

    missing_status, missing_headers, missing_body = asgi_http(app, "/missing", method="HEAD")
    assert missing_status == 404
    assert missing_body == b""
    assert missing_headers["content-length"] == str(len(b"Not Found"))


def test_head_on_a_stream_does_not_send_chunks(tmp_path: Path):
    from tests.asgi_http import asgi_http

    class StreamPage:
        def render(self):
            def gen():
                yield "<p>hi</p>"

            return gen()

    core = DirectoryRoutes(tmp_path)
    core.records = [
        RouteRecord(
            method="GET",
            path="/g",
            name="StreamPage",
            page_cls=StreamPage,
            kind="page",
        )
    ]
    status, _headers, body = asgi_http(DirectoryASGI(core), "/g", method="HEAD")
    assert status == 200
    assert body == b""


def test_unknown_cek_mode_does_not_attach_a_channel():
    from ux_compose import App

    app = App()
    with pytest.raises(ValueError, match="off, adapt, or require"):
        app.use_cek(mode="banana")
    assert app._channel is None
    assert int(app.level) == 0


def test_clear_shared_state_reports_sqlite_without_kv(tmp_path: Path, monkeypatch, caplog):
    from ux_compose.cli.serve_state import STATE_STORE_ENV, clear_shared_state

    path = tmp_path / "empty.sqlite"
    sqlite3.connect(path).close()
    monkeypatch.setenv(STATE_STORE_ENV, str(path))
    with caplog.at_level(logging.ERROR):
        ok = clear_shared_state()
    assert ok is False
    assert path.exists()
    assert "clear_shared_state" in caplog.text


def test_clear_shared_state_returns_true_when_kv_is_cleared(tmp_path: Path, monkeypatch):
    from ux_compose.cli.serve_state import STATE_STORE_ENV, clear_shared_state

    path = tmp_path / "bag.sqlite"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE kv (k TEXT PRIMARY KEY, v TEXT, ver INTEGER)")
    conn.execute("INSERT INTO kv VALUES ('n', '1', 1)")
    conn.commit()
    conn.close()
    monkeypatch.setenv(STATE_STORE_ENV, str(path))
    assert clear_shared_state() is True
    conn = sqlite3.connect(path)
    assert conn.execute("SELECT COUNT(*) FROM kv").fetchone()[0] == 0
    conn.close()


def test_doctor_snippet_names_diagnostics():
    from ux_compose.doctor import DoctorResult

    text = (ROOT / "docs" / "guides" / "SNIPPETS.md").read_text(encoding="utf-8")
    start = text.index("### doctor() laws")
    end = text.index("### uxcompose CLI", start)
    block = text[start:end]
    assert "result.issues" not in block
    assert "result.diagnostics" in block
    assert "diagnostics" in DoctorResult.__dataclass_fields__
    assert "issues" not in DoctorResult.__dataclass_fields__


def test_directory_router_error_alias_is_gone():
    import ux_compose.routing as routing

    assert not hasattr(routing, "DirectoryRouterError")
