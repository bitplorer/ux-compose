"""Regression: nothing is published, so no tombstones, aliases or private imports.

ux-dom ADR 0004: a removed name is simply gone. An unknown value gets the
one generic error, never a message that teaches the old name.
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src" / "ux_compose"
sys.path.insert(0, str(ROOT / "src"))

SPECIALISTS = ("ux_dom", "ux_channel", "ux_behavior", "ux_motion", "cek_host", "cek_surface")


def _private(module: str) -> bool:
    parts = module.split(".")
    if parts[0] not in SPECIALISTS:
        return False
    return "src" in parts[1:] or any(p.startswith("_") and not p.startswith("__") for p in parts)


def test_src_imports_only_public_specialist_modules():
    hits = []
    for path in sorted(SRC.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                mods = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            else:
                continue
            hits += [f"{path.relative_to(ROOT)}:{node.lineno} {m}" for m in mods if _private(m)]
    assert hits == []


@pytest.mark.parametrize(
    "module",
    ["ux_dom.dom.src.component", "ux_dom._x", "ux_channel.wire._codec", "ux_dom.dom.src"],
)
def test_private_guard_catches(module):
    assert _private(module)


@pytest.mark.parametrize("module", ["ux_dom.dom", "ux_dom", "importlib._bootstrap", "ux_compose.cli._ports"])
def test_private_guard_ignores(module):
    assert not _private(module)


@pytest.mark.parametrize("host", ["batteries", "directory_router", "starlette"])
def test_unknown_host_gets_the_generic_error(host, tmp_path):
    from ux_compose.routing import host as host_mod
    from ux_compose.surfaces_host import attach_page_router

    with pytest.raises(ValueError, match="use auto\\|fastapi\\|asgi") as exc:
        host_mod.open(name="Shop", host=host)
    assert "DirectoryRouter" not in str(exc.value)
    with pytest.raises(ValueError, match="use auto\\|fastapi\\|asgi"):
        attach_page_router(
            asgi_app=None, package_dir=tmp_path, base_directory="routes",
            unit_registry={}, host=host,
        )


def test_batteries_tombstone_is_gone():
    from ux_compose.routing import host as host_mod
    import ux_compose.surfaces_host as surfaces_host

    for mod in (host_mod, surfaces_host):
        assert not hasattr(mod, "ProductBatteriesRejected")
        assert not hasattr(mod, "_BATTERIES_TEACH")


def test_doctor_has_no_leftover_teaching_scanners():
    d = importlib.import_module("ux_compose.doctor")  # the package re-exports doctor()

    for name in ("scan_leftover_aliases", "scan_kit_product_imports", "_LEFTOVER_TOKENS"):
        assert not hasattr(d, name), name
        assert name not in d.__all__
