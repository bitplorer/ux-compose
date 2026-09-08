"""create-app → uxcompose add dialog|actionsheet --page → import routes.*

Atelier E2E: rewritten ``from .overlay import`` must copy kit/overlay.py.
overlay is not a catalog widget; authors must not copy it by hand.
"""
from __future__ import annotations

import importlib
import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main
from ux_compose.kit.catalog import CATALOG
from ux_compose.scaffold import create_app

_APP_MODS = ("routes", "components", "app", "document", "settings")


def _drop_app_modules() -> None:
    for key in list(sys.modules):
        if key in _APP_MODS or key.startswith(("routes.", "components.")):
            sys.modules.pop(key, None)


@contextmanager
def _import_from_app(root: Path):
    inserted = str(root)
    sys.path.insert(0, inserted)
    _drop_app_modules()
    try:
        yield
    finally:
        _drop_app_modules()
        if inserted in sys.path:
            sys.path.remove(inserted)


def test_overlay_stays_out_of_catalog():
    assert "overlay" not in CATALOG


def test_create_app_add_dialog_page_imports_without_manual_overlay(tmp_path: Path):
    root = create_app(tmp_path / "shop", name="shop", level=1, host="asgi")
    assert main(["add", "dialog", "--page", "--root", str(root)]) == 0
    assert (root / "components" / "dialog.py").is_file()
    assert (root / "components" / "overlay.py").is_file()
    assert (root / "routes" / "dialog.py").is_file()
    assert not (root / "routes" / "overlay.py").exists()
    with _import_from_app(root):
        mod = importlib.import_module("routes.dialog")
        assert hasattr(mod, "Dialog")


def test_create_app_add_actionsheet_page_imports_without_manual_overlay(tmp_path: Path):
    root = create_app(tmp_path / "sheetapp", name="sheetapp", level=1, host="asgi")
    assert main(["add", "actionsheet", "--page", "--root", str(root)]) == 0
    assert (root / "components" / "actionsheet.py").is_file()
    assert (root / "components" / "overlay.py").is_file()
    assert (root / "routes" / "actionsheet.py").is_file()
    with _import_from_app(root):
        mod = importlib.import_module("routes.actionsheet")
        assert hasattr(mod, "ActionSheet")
