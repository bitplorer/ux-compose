"""Kit expansion: catalog resolve, Document render, a11y smoke, Isolation.

Isolation: this file never imports ux_channel. No Cap kernel / cek-runtime / law.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit.catalog import CATALOG, resolve
from ux_compose.kit.copy import copy_component


KIT_DIR = ROOT / "src" / "ux_compose" / "kit"

P0 = (
    "navbar",
    "navmenu",
    "usermenu",
    "popover",
    "tooltip",
    "alertdialog",
    "formlayout",
    "fieldset",
    "datepicker",
    "switch",
    "card",
    "emptystate",
    "stats",
    "alert",
    "banner",
    "progress",
    "skeleton",
    "hero",
    "footer",
    "cta",
)
P1 = (
    "avatar",
    "badge",
    "hovercard",
    "searchbar",
    "fileupload",
    "tagsinput",
    "multiselect",
    "descriptionlist",
    "featuregrid",
    "testimonials",
    "newsletter",
    "bottomnav",
    "separator",
    "slider",
)
CHROME_A = (
    "menubar",
    "toolbar",
    "togglegroup",
    "spinbutton",
    "themeswitch",
    "filterbar",
)
HARDENED = (
    "dialog",
    "sheet",
    "table",
    "select",
    "tabs",
    "accordion",
    "combobox",
    "dropdown",
    "toast",
    "login",
    "sidebar",
    "actionsheet",
    "contextmenu",
    "command",
)


def _boot(*classes, **kwargs):
    app = App.boot("KitExpand", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def _cls(stem: str):
    meta = CATALOG[stem]
    mod = __import__(meta["module"], fromlist=[meta["name"]])
    return getattr(mod, meta["name"])


def test_add_targets_resolve():
    for stem in (*HARDENED, *P0, *P1, *CHROME_A, "drawer"):
        meta = resolve(stem)
        assert meta["stem"] == stem or meta["name"].lower() == stem
        assert meta["css"] is False
        assert meta["page"] is True
    assert resolve("user-menu")["stem"] == "usermenu"
    assert resolve("alert-dialog")["stem"] == "alertdialog"
    assert resolve("empty-state")["stem"] == "emptystate"
    assert resolve("toggle-group")["stem"] == "togglegroup"
    assert resolve("theme-switch")["stem"] == "themeswitch"


def test_overlay_stays_out_of_catalog():
    assert "overlay" not in CATALOG
    assert "catalog" not in CATALOG
    assert "copy" not in CATALOG


def test_new_kits_render_document_path():
    from ux_compose.helpers import _serialize_tree

    for stem in (*P0, *P1, *CHROME_A, "drawer"):
        cls = _cls(stem)
        tree = cls().render()
        assert not isinstance(tree, str), stem
        html = _serialize_tree(tree)
        assert f'id="{cls.id}"' in html or f"id='{cls.id}'" in html, stem
        lower = html.lower()
        assert "<html" not in lower
        assert "<!doctype" not in lower
        assert "ux_channel" not in html


def test_a11y_smoke_roles_and_labels():
    app = _boot(
        _cls("dialog"),
        _cls("table"),
        _cls("tabs"),
        _cls("select"),
        _cls("login"),
        _cls("navbar"),
        _cls("switch"),
        _cls("formlayout"),
        _cls("alert"),
        _cls("alertdialog"),
        _cls("calendar"),
        _cls("fileupload"),
        _cls("combobox"),
        _cls("accordion"),
        _cls("actionsheet"),
        _cls("datepicker"),
        _cls("plans"),
        _cls("contextmenu"),
        _cls("command"),
        strict_caps=False,
    )
    app.dispatch("dialog.ask", id="oak-02")
    dialog = _html(app, "dialog")
    assert 'role="dialog"' in dialog
    assert 'aria-modal="true"' in dialog
    assert "aria-labelledby" in dialog
    assert "aria-describedby" in dialog
    assert "keydown.escape" in dialog
    assert 'tabindex="-1"' in dialog

    table = _html(app, "table")
    assert "<table" in table
    assert 'scope="col"' in table
    assert "Select all rows" in table
    assert 'role="checkbox"' in table
    assert "aria-checked" in table
    assert "Select Work shirt" in table
    assert "table.toggle_all" in table
    assert "table.toggle_row" in table
    row_tag = table[table.find('id="row-oak-02"'):table.find(">", table.find('id="row-oak-02"'))]
    assert "table.toggle_row" not in row_tag

    tabs = _html(app, "tabs")
    assert 'role="tablist"' in tabs
    assert 'role="tab"' in tabs
    assert 'role="tabpanel"' in tabs
    assert 'id="tabs-tab-overview"' in tabs
    assert 'aria-controls="tabs-p-overview"' in tabs
    assert 'id="tabs-p-overview"' in tabs
    assert 'id="tabs-tab-work"' in tabs
    assert 'aria-controls="tabs-p-work"' in tabs
    assert 'id="tabs-p-work"' in tabs
    assert 'id="tabs-p-billing"' in tabs
    assert tabs.count('role="tabpanel"') == 3
    assert "hidden" in tabs

    login = _html(app, "login")
    assert 'for="login-email"' in login or "html_for" in login
    assert 'id="login-email"' in login
    assert 'id="login-tab-login"' in login
    assert 'aria-controls="login-p-login"' in login
    assert 'id="login-p-login"' in login
    assert 'id="login-tab-signup"' in login
    assert 'aria-controls="login-p-signup"' in login
    assert 'id="login-p-signup"' in login
    assert 'role="tabpanel"' in login

    navbar = _html(app, "navbar")
    assert 'aria-label="Primary"' in navbar
    closed_desk = navbar.count('href="/desk"')
    app.dispatch("navbar.toggle")
    navbar = _html(app, "navbar")
    assert navbar.count('href="/desk"') == closed_desk + 1
    switch = _html(app, "switch")
    assert 'role="switch"' in switch
    form = _html(app, "formlayout")
    assert 'for="formlayout-email"' in form or 'id="formlayout-email"' in form
    alert = _html(app, "alert")
    assert 'role="alert"' in alert

    app.dispatch("alertdialog.ask")
    interrupt = _html(app, "alertdialog")
    assert 'role="alertdialog"' in interrupt
    assert "Keep it" in interrupt
    assert "Delete" in interrupt
    assert "keydown.escape" not in interrupt
    assert "alertdialog.cancel" in interrupt
    scrim_tag = interrupt[interrupt.find('id="alertdialog-scrim"'):interrupt.find(">", interrupt.find('id="alertdialog-scrim"'))]
    assert "alertdialog.cancel" not in scrim_tag

    calendar = _html(app, "calendar")
    assert 'role="grid"' in calendar
    assert 'aria-selected="true"' in calendar

    upload = _html(app, "fileupload")
    assert 'for="fileupload-file"' in upload or 'id="fileupload-file"' in upload
    assert "Demo names sketch.png" in upload

    combo = _html(app, "combobox")
    assert 'id="combobox-form"' in combo
    acc = _html(app, "accordion")
    assert 'id="accordion-fit"' in acc
    assert 'id="accordion-h-fit"' in acc
    assert 'id="accordion-p-fit"' in acc

    app.dispatch("actionsheet.open_sheet")
    sheet = _html(app, "actionsheet")
    assert "autofocus" in sheet
    assert 'id="actionsheet-panel"' in sheet

    app.dispatch("select.toggle")
    select = _html(app, "select")
    assert 'for="select-trigger"' in select
    assert 'id="select-trigger"' in select

    app.dispatch("datepicker.toggle")
    picker = _html(app, "datepicker")
    assert 'role="row"' in picker
    assert 'role="gridcell"' in picker

    plans = _html(app, "plans")
    assert 'role="radiogroup"' in plans
    assert 'role="radio"' in plans
    assert "aria-checked" in plans

    app.dispatch("contextmenu.open_menu")
    ctx = _html(app, "contextmenu")
    assert 'aria-controls="contextmenu-menu"' in ctx
    assert 'id="contextmenu-menu"' in ctx

    app.dispatch("command.open_pal")
    pal = _html(app, "command")
    assert "command.sign_out" in pal
    assert "Sign out" in pal


def test_table_row_click_is_not_select_all():
    Table = _cls("table")
    app = _boot(Table, strict_caps=False)
    app.dispatch("table.toggle_row", sku="oak-02")
    inst = app.behavior.get("table")
    assert tuple(inst.selected or ()) == ("oak-02",)
    app.dispatch("table.toggle_all")
    selected = set(inst.selected or ())
    assert selected == {"linen-01", "oak-02", "wool-03", "clay-04"}
    app.dispatch("table.toggle_row", sku="oak-02")
    assert "oak-02" not in set(inst.selected or ())
    assert "linen-01" in set(inst.selected or ())
    html = _html(app, "table")
    assert "Select all rows" in html
    assert 'id="row-oak-02"' in html
    assert 'role="checkbox"' in html
    assert 'aria-checked="true"' in html
    assert "table.toggle_all" in html
    assert "table.toggle_row" in html
    row_tag = html[html.find('id="row-oak-02"'):html.find(">", html.find('id="row-oak-02"'))]
    assert "table.toggle_row" not in row_tag


def test_kit_modules_never_import_ux_channel():
    forbidden = ("ux_channel", "cek_runtime", "cek_host")
    for path in sorted(KIT_DIR.glob("*.py")):
        src = path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(alias.name.startswith(f) for f in forbidden), path
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not any(node.module.startswith(f) for f in forbidden), path


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_copy_new_kit_and_drawer_sibling(tmp_path: Path):
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    written = copy_component("navbar", root=tmp_path)
    assert written["py"].is_file()
    ast.parse(written["py"].read_text(encoding="utf-8"))
    drawer = copy_component("drawer", root=tmp_path)
    assert drawer["py"].is_file()
    assert (tmp_path / "components" / "sheet.py").is_file()
    text = drawer["py"].read_text(encoding="utf-8")
    assert "from .sheet import" in text
    assert "from ux_compose.kit.sheet import" not in text
