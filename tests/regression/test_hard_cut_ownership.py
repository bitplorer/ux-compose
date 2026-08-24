"""Regression: product lifecycle stays on uxcompose; HMR not Document API."""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main
from ux_compose import hmr
from ux_compose.app import App
from ux_compose.doctor import doctor
from ux_compose.surfaces import mount_surfaces


def test_cli_has_product_commands_only_in_help(capsys):
    main(["--help"])
    out = capsys.readouterr().out
    assert "create-app" in out
    assert "serve" in out
    assert "deploy" in out
    assert "doctor" in out
    assert "build" in out
    assert "os.execvp" not in out
    assert "uxdom serve" not in out
    assert "uxdom build" not in out
    assert "ux_compose.tailwind" in out


def test_hmr_is_delivery_module():
    assert hasattr(hmr, "attach_hmr")
    assert hasattr(hmr, "client_script_tag")
    # HMR path is compose-owned, not a Document.use symbol
    assert hmr.HMR_PATH.startswith("/__uxcompose")


def test_dx_doc_is_sole_product_cli():
    text = (ROOT / "docs" / "guides" / "DX.md").read_text(encoding="utf-8")
    assert "os.execvp" not in text
    assert "prefer specialist ceremony" not in text
    assert "uxcompose create-app" in text
    assert "DirectoryRoutes" in text
    assert "uxcompose build" in text
    assert "ux_compose.tailwind" in text or "compiler" in text.lower()


def test_index_owns_product_build_and_compiler():
    text = (ROOT / "docs" / "INDEX.md").read_text(encoding="utf-8")
    assert "`create-app`, `build`, `serve`, `deploy`, `doctor`" in text
    assert "Tailwind CLI finder" in text
    assert "leftover `uxdom build`" in text


def test_internals_flow_defers_to_canonical():
    text = (ROOT / "docs" / "internals" / "FLOW.md").read_text(encoding="utf-8")
    assert "FLOW.md wins" in text or "../FLOW.md" in text
    assert "ux_compose.tailwind" in text
    assert "create-app · build · serve · deploy" in text


def test_webassets_lives_on_compose():
    from ux_compose import WebAssets
    from ux_compose.assets import WebAssets as WA

    assert WebAssets is WA
    src = (ROOT / "src" / "ux_compose" / "scaffold.py").read_text(encoding="utf-8")
    assert "from ux_compose import WebAssets" in src
    assert "from ux_dom import WebAssets" not in src
    doc = (ROOT / "docs" / "FLOW.md").read_text(encoding="utf-8")
    assert "WebAssets" in doc
    assert "ux_compose.assets" in doc or "asset layout" in doc.lower()
    dx = (ROOT / "docs" / "guides" / "DX.md").read_text(encoding="utf-8")
    assert "WebAssets folders" not in dx
    tw = (ROOT / "docs" / "guides" / "TAILWIND.md").read_text(encoding="utf-8")
    assert "from ux_dom import WebAssets" not in tw
    assert "from ux_compose import WebAssets" in tw
    assert "webassets=webassets" not in tw


def test_doctor_teaches_directory_routes_not_router():
    report = doctor([], fail=False)
    assert "directory_router" not in report.capabilities
    assert "directory_routes" in report.capabilities
    joined = " ".join(report.teaching)
    assert "DirectoryRouter via" not in joined
    if report.capabilities.get("directory_routes") or report.capabilities.get("ux_dom"):
        assert "DirectoryRoutes" in joined or "page-unit" in joined.lower()


def test_bind_pages_alias_still_accepted():
    assert "bind_pages" in inspect.signature(App.mount).parameters
    assert "include_directory_router" in inspect.signature(App.mount).parameters
    assert "bind_pages" in inspect.signature(mount_surfaces).parameters
    assert "include_directory_router" in inspect.signature(mount_surfaces).parameters
