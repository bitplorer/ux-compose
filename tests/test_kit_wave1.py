"""Wave-1 kit: action sheet, context menu, typeahead, pull-to-refresh."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.kit import ActionSheet, ContextMenu, PullRefresh, Typeahead


def _boot(*classes, **kwargs):
    app = App.boot("KitWave1", **kwargs)
    app.add(*classes)
    return app


def _html(app, cid: str) -> str:
    inst = app.behavior.get(cid)
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return str(inst.render())


def test_actionsheet_open_pick_close():
    app = _boot(ActionSheet, strict_caps=False)
    html = _html(app, "actionsheet")
    assert "Open actions" in html
    assert "Share this piece" not in html
    app.dispatch("actionsheet.open_sheet")
    html = _html(app, "actionsheet")
    assert "Share this piece" in html
    assert "Dismiss" in html
    assert "swipe.vertical" in html
    assert "swipe.down" in html
    assert 'id="actionsheet-panel"' in html
    assert 'id="actionsheet-scrim"' in html
    assert 'id="actionsheet-dismiss"' in html
    assert "relative" not in ActionSheet.class_card
    app.dispatch("actionsheet.pick", key="share")
    inst = app.behavior.get("actionsheet")
    assert str(inst.picked) == "share"
    assert not bool(inst.open)
    html = _html(app, "actionsheet")
    assert "Last pick" in html


def test_actionsheet_archive_is_cap():
    app = _boot(ActionSheet, strict_caps=True)
    with pytest.raises(Exception):
        app.dispatch("actionsheet.archive", key="archive")
    app = _boot(ActionSheet, strict_caps=False)
    app.dispatch("actionsheet.archive", key="archive")
    inst = app.behavior.get("actionsheet")
    assert str(inst.picked) == "archive"


def test_contextmenu_longpress_attr_on_trigger_only():
    app = _boot(ContextMenu, strict_caps=False)
    html = _html(app, "contextmenu")
    assert "click longpress" in html
    app.dispatch("contextmenu.open_menu")
    html = _html(app, "contextmenu")
    assert "Rename" in html
    assert "list-none" in html
    # host must not broadcast longpress to items
    assert html.count("click longpress") == 1
    assert html.count("data-channel-on") == 1 or html.count("data_channel_on") <= 1
    app.dispatch("contextmenu.run", key="rename")
    inst = app.behavior.get("contextmenu")
    assert str(inst.ran) == "rename"
    assert not bool(inst.open)


def test_typeahead_query_and_pick():
    app = _boot(Typeahead, strict_caps=False)
    html = _html(app, "typeahead")
    assert "input delay:300" in html
    assert "Linen work shirt" in html
    app.dispatch("typeahead.query_hits", q="oak")
    html = _html(app, "typeahead")
    assert "Oak serving board" in html
    assert "Clay pourer" not in html
    app.dispatch("typeahead.query_hits", q="l")
    html = _html(app, "typeahead")
    assert "Linen work shirt" in html
    assert "Wool throw" not in html
    app.dispatch("typeahead.query_hits", q="")
    html = _html(app, "typeahead")
    assert "Oak serving board" in html
    app.dispatch("typeahead.pick", key="Oak stool")
    inst = app.behavior.get("typeahead")
    assert str(inst.value) == "Oak stool"


def test_pullrefresh_grows_then_catches():
    app = _boot(PullRefresh, strict_caps=False)
    html = _html(app, "pullrefresh")
    assert "swipe.vertical" in html
    assert "swipe.down" in html
    inst = app.behavior.get("pullrefresh")
    n0 = len(inst._rows())
    app.dispatch("pullrefresh.refresh")
    assert len(inst._rows()) == n0 + 1
    for _ in range(8):
        app.dispatch("pullrefresh.refresh")
    assert str(inst.phase) == "caught"
    html = _html(app, "pullrefresh")
    assert "Caught up" in html
