"""OverlayChrome is the shared overlay primitive — widgets adopt later."""
from __future__ import annotations

from ux_compose.kit.overlay import OverlayChrome, overlay


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
    # Root swipe is the defect this primitive exists to prevent.
    assert not grammar.startswith("swipe.")


def test_open_plan_degrades_without_motion():
    chrome = overlay("dialog")
    # Offline / no ux-motion: None is correct, not an exception.
    plan = chrome.open_plan()
    assert plan is None or hasattr(plan, "enter")
