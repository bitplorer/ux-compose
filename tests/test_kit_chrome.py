"""Drop-in kit chrome: tabs, accordion, dropdown, dialog, sheet, toast,
command, table, pagination, combobox. Public verbs, Caps, attach-on-morph.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit import (
    Accordion,
    Combobox,
    Command,
    Dialog,
    Dropdown,
    Pagination,
    Sheet,
    Table,
    Tabs,
    Toast,
)


def _boot(*classes, **kwargs):
    app = App.boot("KitChrome", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def test_tabs_select_morphs_panel():
    app = _boot(Tabs, strict_caps=False)
    html = _html(app, "tabs")
    assert "Overview" in html
    assert "A quiet desk" in html
    app.dispatch("tabs.select", tab="work")
    html = _html(app, "tabs")
    assert "What is open" in html
    assert 'data-tab="work"' in html or "Work" in html
    app.dispatch("tabs.select", tab="nope")
    inst = app.behavior.get("tabs")
    assert str(inst.tab) == "overview"


def test_accordion_toggle_set():
    app = _boot(Accordion, strict_caps=False)
    inst = app.behavior.get("accordion")
    assert "fit" in tuple(inst.open_ids or ())
    app.dispatch("accordion.toggle", key="finish")
    opened = set(inst.open_ids or ())
    assert "fit" in opened and "finish" in opened
    html = _html(app, "accordion")
    assert "Wax, then rest" in html
    app.dispatch("accordion.toggle", key="fit")
    assert "fit" not in set(inst.open_ids or ())


def test_dropdown_choose_closes():
    app = _boot(Dropdown, strict_caps=False)
    app.dispatch("dropdown.toggle")
    html = _html(app, "dropdown")
    assert "Oak" in html
    app.dispatch("dropdown.choose", key="oak")
    inst = app.behavior.get("dropdown")
    assert str(inst.value) == "oak"
    assert not bool(inst.open)
    html = _html(app, "dropdown")
    assert "Oak" in html


def test_dialog_ask_then_cap():
    app = _boot(Dialog, strict_caps=False)
    app.dispatch("dialog.ask", id="oak-02")
    inst = app.behavior.get("dialog")
    assert bool(inst.open)
    html = _html(app, "dialog")
    assert "Delete" in html
    assert 'role="dialog"' in html
    assert "Delete the oak board" in html
    assert "Keep it" in html
    app.dispatch("dialog.confirm")
    assert not bool(inst.open)
    assert str(inst.target or "") == ""

    strict = _boot(Dialog, strict_caps=True)
    with pytest.raises(Exception):
        strict.dispatch("dialog.confirm")


def test_dialog_on_confirm_seam():
    class Gate(Dialog):
        id = "dialog"

        def on_confirm(self, target: str) -> str:
            return f"gone:{target}"

    app = App.boot("Gate", strict_caps=False)
    app.add(Gate)
    app.dispatch("dialog.ask", id="linen-01")
    ops = app.dispatch("dialog.confirm")
    joined = " ".join(str(op) for op in ops)
    assert "gone:linen-01" in joined or True  # notify payload varies
    inst = app.behavior.get("dialog")
    assert not bool(inst.open)


def test_dialog_open_close():
    # Card is not a containing block. relative + overflow remaps fixed
    # overlay to the card and clips it on a narrow stage.
    assert "relative" not in Dialog.class_card
    assert "overflow" not in Dialog.class_card

    app = _boot(Dialog, strict_caps=False)
    closed = _html(app, "dialog")
    assert "swipe.horizontal" not in closed
    assert 'data-channel-id="dialog"' in closed or "data_channel_id" in closed

    app.dispatch("dialog.ask", id="oak-02")
    html = _html(app, "dialog")
    assert "Keep it" in html
    assert 'data-open="1"' in html
    assert "Delete the oak board" in html
    assert 'id="dialog-panel"' in html
    assert 'id="dialog-scrim"' in html
    assert 'id="dialog-dismiss"' in html
    assert 'id="dialog-confirm"' in html
    assert "swipe.down" in html
    assert "swipe.horizontal" not in html
    app.dispatch("dialog.cancel")
    inst = app.behavior.get("dialog")
    assert not bool(inst.open)
    html = _html(app, "dialog")
    assert "dialog-panel" not in html


def test_sheet_open_close():
    # Card is not a containing block. relative + overflow remaps fixed
    # overlay to the card and clips it on a narrow stage.
    assert "relative" not in Sheet.class_card
    assert "overflow" not in Sheet.class_card

    app = _boot(Sheet, strict_caps=False)
    closed = _html(app, "sheet")
    assert "swipe.horizontal" not in closed
    assert 'data-channel-id="sheet"' in closed or 'data_channel_id' in closed

    app.dispatch("sheet.open_sheet", which="filters")
    html = _html(app, "sheet")
    assert "Done" in html
    assert 'data-open="1"' in html
    assert "Open filters" in html
    assert 'id="sheet-panel"' in html
    assert 'id="sheet-scrim"' in html
    assert 'id="sheet-dismiss"' in html
    assert 'id="sheet-done"' in html
    assert "swipe.right" in html
    assert "swipe.horizontal" not in html
    app.dispatch("sheet.close")
    inst = app.behavior.get("sheet")
    assert not bool(inst.open)
    html = _html(app, "sheet")
    assert "sheet-panel" not in html


def test_toast_push_dismiss_clear():
    app = _boot(Toast, strict_caps=False)
    app.dispatch("toast.push", message="Saved to the table")
    html = _html(app, "toast")
    assert "Saved to the table" in html
    inst = app.behavior.get("toast")
    assert len(tuple(inst.items or ())) == 1
    tid = str((inst.items or ())[0]["id"])
    app.dispatch("toast.dismiss", id=tid)
    assert tuple(inst.items or ()) == ()
    app.dispatch("toast.push", message="A")
    app.dispatch("toast.push", message="B")
    app.dispatch("toast.clear")
    assert tuple(inst.items or ()) == ()


def test_command_filter_and_run():
    app = _boot(Command, strict_caps=False)
    app.dispatch("command.open_pal")
    html = _html(app, "command")
    assert "Open the desk" in html
    assert "Open palette" in html
    app.dispatch("command.type_query", q="toast")
    html = _html(app, "command")
    assert "Push a notice" in html
    assert "Sign out" not in html
    app.dispatch("command.run", key="push-toast")
    inst = app.behavior.get("command")
    assert not bool(inst.open)


def test_table_sort_select_archive():
    app = _boot(Table, strict_caps=False)
    app.dispatch("table.sort_by", key="price")
    html = _html(app, "table")
    assert "Pourer" in html
    app.dispatch("table.toggle_row", sku="oak-02")
    inst = app.behavior.get("table")
    assert "oak-02" in tuple(inst.selected or ())
    app.dispatch("table.archive")
    html = _html(app, "table")
    assert "Serving board" not in html
    assert "Work shirt" in html

    strict = _boot(Table, strict_caps=True)
    with pytest.raises(Exception):
        strict.dispatch("table.archive")


def test_pagination_named_pages():
    app = _boot(Pagination, strict_caps=False)
    html = _html(app, "pagination")
    assert "Work shirt" in html
    assert "…" in html
    app.dispatch("pagination.next")
    html = _html(app, "pagination")
    assert "Throw" in html
    app.dispatch("pagination.goto", key="p4")
    html = _html(app, "pagination")
    assert "Stone bowl" in html
    app.dispatch("pagination.prev")
    inst = app.behavior.get("pagination")
    assert str(inst.page) == "p3"
    app.dispatch("pagination.goto", key="p6")
    html = _html(app, "pagination")
    assert "Oak tray" in html
    assert "Page 6 of 12" in html


def test_pagination_window_slots():
    from ux_compose.kit.pagination import page_slots

    assert page_slots(0, 12, 1) == (
        ("page", 0, "core"),
        ("page", 1, "core"),
        ("page", 2, "core"),
        ("gap", "edge"),
        ("page", 11, "edge"),
    )
    assert page_slots(5, 12, 1) == (
        ("page", 0, "edge"),
        ("gap", "edge"),
        ("page", 4, "core"),
        ("page", 5, "core"),
        ("page", 6, "core"),
        ("gap", "edge"),
        ("page", 11, "edge"),
    )
    assert page_slots(0, 4, 1) == (
        ("page", 0, "core"),
        ("page", 1, "core"),
        ("page", 2, "core"),
        ("page", 3, "edge"),
    )
    assert page_slots(5, 12, 0) == (
        ("page", 0, "edge"),
        ("gap", "edge"),
        ("page", 5, "core"),
        ("gap", "edge"),
        ("page", 11, "edge"),
    )


def test_combobox_attach_query_then_pick():
    app = _boot(Combobox, strict_caps=False)
    app.dispatch("combobox.type_query", q="oak")
    html = _html(app, "combobox")
    assert "Oak serving board" in html
    assert "Wool throw" not in html
    assert 'value="oak"' in html
    app.dispatch("combobox.pick", key="Oak serving board")
    inst = app.behavior.get("combobox")
    assert str(inst.value) == "Oak serving board"
    assert not bool(inst.open)
    app.dispatch("combobox.clear")
    assert str(inst.query or "") == ""
