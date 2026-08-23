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
    assert "os.execvp" not in out
    assert "uxdom serve" not in out


def test_hmr_is_delivery_module():
    assert hasattr(hmr, "attach_hmr")
    assert hasattr(hmr, "client_script_tag")
    # HMR path is compose-owned, not a Document.use symbol
    assert hmr.HMR_PATH.startswith("/__uxcompose")


def test_dx_doc_is_sole_product_cli():
    text = (ROOT / "docs" / "DX.md").read_text(encoding="utf-8")
    assert "os.execvp" not in text
    assert "prefer specialist ceremony" not in text
    assert "uxcompose create-app" in text
    assert "DirectoryRoutes" in text


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
