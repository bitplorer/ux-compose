"""OverlayChrome is the shared overlay primitive. Widgets adopt it."""
from __future__ import annotations

from ux_compose.kit.overlay import EDGE_SLIDE, HANDLE_SWIPE, OverlayChrome, overlay


def test_ids_are_stable_and_kind_sets_edge():
    modal = overlay("dialog", kind="modal")
    sheet = overlay("sheet", kind="sheet")
    action = overlay("actionsheet", kind="action")
    assert modal.scrim_id == "dialog-scrim"
    assert modal.panel_id == "dialog-panel"
    assert modal.dismiss_id == "dialog-dismiss"
    assert modal.edge == "center"
    assert sheet.edge == "right"
    assert action.edge == "bottom"


def test_swipe_lives_on_dismiss_not_a_root_token():
    sheet = OverlayChrome(kind="sheet", edge="right", root_id="sheet")
    grammar = sheet.swipe_on_dismiss()
    assert "swipe" in grammar
    assert "click" in grammar
    assert not grammar.startswith("swipe.")


def test_handle_grammar_adds_vertical_on_bottom():
    action = overlay("actionsheet", kind="action")
    handle = action.swipe_on_handle()
    assert "swipe.vertical" in handle
    assert "threshold:48" in handle
    assert handle.startswith("click")
    assert action.swipe_on_dismiss() == "click swipe.down"


def test_shipped_slide_distances():
    assert EDGE_SLIDE["right"] == {"x": 28.0}
    assert EDGE_SLIDE["left"] == {"x": -28.0}
    assert EDGE_SLIDE["bottom"] == {"y": 32.0}
    assert EDGE_SLIDE["top"] == {"y": -32.0}
    assert "swipe.vertical" in HANDLE_SWIPE["bottom"]


def test_open_plan_degrades_without_motion():
    chrome = overlay("dialog")
    plan = chrome.open_plan()
    assert plan is None or hasattr(plan, "enter")


def test_dialog_sheet_actionsheet_take_chrome_from_primitive():
    from ux_compose.kit.actionsheet import ActionSheet
    from ux_compose.kit.dialog import Dialog
    from ux_compose.kit.sheet import Sheet

    dialog = Dialog()
    sheet = Sheet()
    action = ActionSheet()
    assert dialog._chrome() == overlay(dialog.id, kind="dialog")
    assert sheet._chrome() == overlay(sheet.id, kind="sheet")
    assert action._chrome() == overlay(action.id, kind="actionsheet")
    assert dialog._chrome().swipe_on_dismiss() == "click swipe.down"
    assert sheet._chrome().swipe_on_dismiss() == "click swipe.right"
    assert action._chrome().swipe_on_handle() == (
        "click swipe.down swipe.vertical threshold:48"
    )
