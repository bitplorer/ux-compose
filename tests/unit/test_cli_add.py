"""uxcompose add — shadcn-style ownable copy from the kit."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose.cli import main
from ux_compose.kit.catalog import CATALOG
from ux_compose.kit.copy import KitCopyError, copy_component, find_app_root


def _fake_app(tmp_path: Path) -> Path:
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    (tmp_path / "routes" / "__init__.py").write_text("", encoding="utf-8")
    css = tmp_path / "assets" / "css"
    css.mkdir(parents=True)
    (css / "input.css").write_text(
        '@import "tailwindcss";\n@source "../../**/*.{py,html}";\n',
        encoding="utf-8",
    )
    return tmp_path


def test_catalog_has_login():
    assert "login" in CATALOG
    assert CATALOG["login"]["module"] == "ux_compose.kit.login"
    assert CATALOG["login"]["css"] is False
    for stem in (
        "tabs",
        "accordion",
        "dropdown",
        "dialog",
        "sheet",
        "toast",
        "command",
        "table",
        "pagination",
        "combobox",
        "sidebar",
        "breadcrumb",
        "stepper",
        "carousel",
        "calendar",
        "select",
        "otp",
        "plans",
        "actionsheet",
        "contextmenu",
        "typeahead",
        "pullrefresh",
        "rating",
        "kanban",
        "timeline",
        "kpi",
        "slider",
        "lightbox",
        "wishlist",
        "progress",
        "empty",
        "presence",
        "chips",
        "skeleton",
    ):
        assert stem in CATALOG
        assert CATALOG[stem]["css"] is False


def test_copy_tabs_into_app(tmp_path: Path):
    root = _fake_app(tmp_path)
    written = copy_component("tabs", root=root)
    text = written["py"].read_text(encoding="utf-8")
    assert "class Tabs" in text
    assert "rounded-3xl" in text
    assert "border-stone-200" in text
    ast.parse(text)
    assert written["css"] is None
    assert written["base"] is None
    inp = (root / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert '@import "./kit.css"' not in inp
    assert '@import "./tabs.css"' not in inp


def test_copy_login_into_app(tmp_path: Path):
    root = _fake_app(tmp_path)
    written = copy_component("login", root=root)
    py = written["py"]
    assert py is not None and py.is_file()
    text = py.read_text(encoding="utf-8")
    assert "class Login" in text
    assert "def authenticate" in text
    assert "from ux_compose.kit import" not in text
    assert "from ux_compose import" in text
    assert "Ownable copy" in text
    ast.parse(text)
    css = written["css"]
    assert css is None
    assert "rounded-3xl" in text
    assert "class_card" in text
    inp = (root / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert '@import "./login.css"' not in inp
    assert (root / "components" / "__init__.py").is_file()
    assert written["page"] is None  # --page not set; existing route not invented


def test_copy_refuses_overwrite(tmp_path: Path):
    root = _fake_app(tmp_path)
    copy_component("login", root=root)
    with pytest.raises(KitCopyError):
        copy_component("login", root=root)
    copy_component("login", root=root, force=True)


def test_copy_page_unit(tmp_path: Path):
    root = _fake_app(tmp_path)
    written = copy_component("login", root=root, as_page=True)
    page = written["page"]
    assert page is not None and page.is_file()
    text = page.read_text(encoding="utf-8")
    assert "from components.login import Login as LoginCard" in text
    assert "class Login(LoginCard)" in text


def test_force_without_page_preserves_existing_route(tmp_path: Path):
    """Lumen-style: product page unit (desk, channelize) must survive --force."""
    root = _fake_app(tmp_path)
    page = root / "routes" / "login.py"
    marker = "# product page unit — desk + channelize\n"
    page.write_text(marker, encoding="utf-8")
    written = copy_component("login", root=root, force=True, as_page=False)
    assert page.read_text(encoding="utf-8") == marker
    assert written["py"].is_file()
    assert "class Login" in written["py"].read_text(encoding="utf-8")


def test_find_app_root_from_nested(tmp_path: Path):
    root = _fake_app(tmp_path)
    nested = root / "routes"
    assert find_app_root(nested) == root.resolve()


def test_copy_unknown():
    with pytest.raises(KitCopyError):
        copy_component("not-a-real-widget", root=Path("/tmp"))


def test_cli_add_list(capsys, tmp_path: Path):
    assert main(["add", "--list"]) == 0
    out = capsys.readouterr().out
    assert "login" in out
    assert "Sign-in" in out or "sign" in out.lower()


def test_cli_add_login(tmp_path: Path, capsys):
    root = _fake_app(tmp_path)
    assert main(["add", "login", "--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "wrote py:" in out
    assert (root / "components" / "login.py").is_file()


def test_cli_add_unknown(capsys):
    assert main(["add", "nope"]) == 1
    err = capsys.readouterr().err
    assert "unknown" in err.lower()


def test_help_mentions_add(capsys):
    assert main(["--help"]) == 0
    out = capsys.readouterr().out
    assert "uxcompose add" in out
