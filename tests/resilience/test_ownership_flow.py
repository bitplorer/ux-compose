"""OWN/REG — FLOW law: product lifecycle is compose-only; HMR is delivery."""
from __future__ import annotations

import inspect
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_flow_doc_declares_ownership_law():
    text = (ROOT / "docs" / "FLOW.md").read_text(encoding="utf-8")
    assert "ux-dom" in text and "RENDER" in text
    assert "ux-compose" in text and "PRODUCT" in text
    assert "create-app" in text
    assert "DirectoryRoutes" in text


def test_hard_cut_regression_module_present():
    p = ROOT / "tests" / "regression" / "test_hard_cut_ownership.py"
    assert p.is_file()
    body = p.read_text(encoding="utf-8")
    assert "create-app" in body
    assert "DirectoryRoutes" in body or "directory_routes" in body


def test_app_mount_keeps_bind_pages_alias():
    from ux_compose.app import App
    from ux_compose.surfaces import mount_surfaces

    assert "bind_pages" in inspect.signature(App.mount).parameters
    assert "include_directory_router" in inspect.signature(App.mount).parameters
    assert "bind_pages" in inspect.signature(mount_surfaces).parameters


def test_hmr_path_is_compose_delivery():
    from ux_compose import hmr

    assert hasattr(hmr, "attach_hmr")
    assert hmr.HMR_PATH.startswith("/__uxcompose")
