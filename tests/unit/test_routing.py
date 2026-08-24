"""DirectoryRoutes lives on ux-compose (product page-unit path)."""
from __future__ import annotations

from pathlib import Path

import pytest

from ux_compose.routing import DirectoryRoutes, RouterHooks
from ux_compose.surfaces_host import ProductBatteriesRejected, attach_page_router


def test_directory_routes_exported_from_compose():
    from ux_compose import DirectoryASGI, DirectoryRoutes as DR, RouterHooks as RH

    assert DR is DirectoryRoutes
    assert RH is RouterHooks
    from ux_compose.routing.adapters.asgi import DirectoryASGI as ASGI

    assert DirectoryASGI is ASGI


def test_discover_stem_match(tmp_path: Path):
    pkg = tmp_path / "shop"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(
        "class Hello:\n"
        "    def render(self):\n"
        "        return 'hello-ok'\n",
        encoding="utf-8",
    )
    (routes / "_skip.py").write_text(
        "class Skip:\n"
        "    def render(self):\n"
        "        return 'nope'\n",
        encoding="utf-8",
    )
    core = DirectoryRoutes(pkg, base_directory="routes")
    recs = core.discover()
    paths = {r.path for r in recs}
    assert "/hello" in paths
    assert "/_skip" not in paths
    table = core.route_table()
    assert any(row["path"] == "/hello" and row["method"] == "GET" for row in table)


def test_batteries_host_fails_closed():
    with pytest.raises(ProductBatteriesRejected) as ctx:
        attach_page_router(
            asgi_app=object(),
            package_dir=".",
            base_directory="routes",
            unit_registry={},
            host="batteries",
        )
    msg = str(ctx.value)
    assert "DirectoryRoutes" in msg or "ux_compose.routing" in msg


def test_fastapi_adapter_binds_stem_path(tmp_path: Path):
    pytest.importorskip("fastapi")

    from ux_compose.routing.adapters.fastapi import materialize

    pkg = tmp_path / "shop"
    routes = pkg / "routes"
    routes.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(
        "class Hello:\n"
        "    def render(self):\n"
        "        return 'hello-ok'\n",
        encoding="utf-8",
    )
    core = DirectoryRoutes(pkg, base_directory="routes", hooks=RouterHooks())
    core.discover()
    router = materialize(core)
    paths = [getattr(r, "path", None) for r in router.routes]
    assert "/hello" in paths
