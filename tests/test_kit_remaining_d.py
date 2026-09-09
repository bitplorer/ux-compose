"""Kit Batch D P2 leftovers.

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


P2_D = (
    "chart",
    "resizable",
    "tree",
    "colorpicker",
    "fab",
    "diff",
    "countdown",
    "mockup",
    "attachment",
    "scrollarea",
    "feed",
)


def _boot(*classes, **kwargs):
    app = App.boot("KitP2D", **kwargs)
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


def test_p2_d_resolve():
    for stem in P2_D:
        meta = resolve(stem)
        assert meta["stem"] == stem
        assert meta["css"] is False
        assert meta["page"] is True
    assert resolve("treeview")["stem"] == "tree"
    assert resolve("color-picker")["stem"] == "colorpicker"
    assert resolve("scroll-area")["stem"] == "scrollarea"


def test_p2_d_document_trees():
    from ux_compose.algebra import _serialize_tree

    for stem in P2_D:
        cls = _cls(stem)
        tree = cls().render()
        assert not isinstance(tree, str), stem
        html = _serialize_tree(tree)
        assert f'id="{cls.id}"' in html, stem
        assert "ux_channel" not in html


def test_chart_svg_labelled():
    app = _boot(_cls("chart"), strict_caps=False)
    html = _html(app, "chart")
    assert "<svg" in html
    assert "aria-label" in html
    app.dispatch("chart.choose", key="oak")
    assert str(app.behavior.get("chart").which) == "oak"


def test_resizable_named_split():
    app = _boot(_cls("resizable"), strict_caps=False)
    html = _html(app, "resizable")
    assert 'role="separator"' in html or "aria-label" in html
    assert 'role="radiogroup"' in html
    assert 'role="radio"' in html
    assert 'aria-checked="true"' in html
    assert 'aria-checked="false"' in html
    app.dispatch("resizable.split", key="wide")
    assert str(app.behavior.get("resizable").value) == "wide"
    html = _html(app, "resizable")
    assert 'data-value="wide"' in html
    assert 'aria-checked="true"' in html


def test_tree_apg():
    app = _boot(_cls("tree"), strict_caps=False)
    html = _html(app, "tree")
    assert 'role="tree"' in html
    assert 'role="treeitem"' in html
    assert "aria-expanded" in html
    app.dispatch("tree.toggle", key="house")
    app.dispatch("tree.select", key="oak")
    inst = app.behavior.get("tree")
    assert str(inst.selected) == "oak"
    html = _html(app, "tree")
    assert "aria-selected" in html


def test_colorpicker_radios():
    app = _boot(_cls("colorpicker"), strict_caps=False)
    html = _html(app, "colorpicker")
    assert 'role="radiogroup"' in html
    assert 'for="colorpicker-hex"' in html or 'id="colorpicker-hex"' in html
    app.dispatch("colorpicker.choose", key="oak")
    assert str(app.behavior.get("colorpicker").value) == "oak"


def test_fab_menu():
    app = _boot(_cls("fab"), strict_caps=False)
    html = _html(app, "fab")
    assert "aria-haspopup" in html
    assert 'aria-expanded="false"' in html
    assert 'aria-controls="fab-menu"' in html
    # Closed: menu id stays in the tree (menubar-before-#61 dangling-id hole).
    assert 'id="fab-menu"' in html
    assert 'role="menu"' in html
    assert 'hidden="hidden"' in html
    app.dispatch("fab.toggle")
    html = _html(app, "fab")
    assert 'aria-expanded="true"' in html
    assert 'id="fab-menu"' in html
    assert 'role="menu"' in html
    assert "New note" in html
    assert 'hidden="hidden"' not in html
    app.dispatch("fab.run", key="note")
    inst = app.behavior.get("fab")
    assert str(inst.value) == "note"
    assert not bool(inst.open)
    html = _html(app, "fab")
    assert 'id="fab-menu"' in html
    assert 'aria-expanded="false"' in html
    assert 'hidden="hidden"' in html


def test_diff_named_side():
    app = _boot(_cls("diff"), strict_caps=False)
    html = _html(app, "diff")
    assert 'role="radiogroup"' in html or "aria-label" in html
    app.dispatch("diff.choose", key="after")
    assert str(app.behavior.get("diff").which) == "after"


def test_countdown_refstate():
    app = _boot(_cls("countdown"), strict_caps=False)
    html = _html(app, "countdown")
    assert 'role="timer"' in html or "aria-live" in html
    inst = app.behavior.get("countdown")
    n = int(inst.remain or 0)
    app.dispatch("countdown.tick")
    assert int(inst.remain) == max(0, n - 1)


def test_mockup_named_device():
    app = _boot(_cls("mockup"), strict_caps=False)
    html = _html(app, "mockup")
    assert 'role="radiogroup"' in html
    app.dispatch("mockup.choose", key="phone")
    assert str(app.behavior.get("mockup").value) == "phone"


def test_attachment_list_refstate():
    app = _boot(_cls("attachment"), strict_caps=False)
    html = _html(app, "attachment")
    assert 'for="attachment-file"' in html or 'id="attachment-file"' in html
    app.dispatch("attachment.add", name="sketch.png")
    inst = app.behavior.get("attachment")
    assert "sketch.png" in tuple(inst.files or ())
    app.dispatch("attachment.remove", name="sketch.png")
    assert "sketch.png" not in tuple(inst.files or ())


def test_scrollarea_labelled():
    app = _boot(_cls("scrollarea"), strict_caps=False)
    html = _html(app, "scrollarea")
    assert 'tabindex="0"' in html
    assert "aria-label" in html
    app.dispatch("scrollarea.jump", key="end")
    assert str(app.behavior.get("scrollarea").which) == "end"


def test_feed_articles():
    app = _boot(_cls("feed"), strict_caps=False)
    html = _html(app, "feed")
    assert 'role="feed"' in html
    assert 'role="article"' in html
    app.dispatch("feed.append")
    inst = app.behavior.get("feed")
    assert len(tuple(inst.items or ())) >= 2


def test_a11y_and_caps_p2_d():
    app = _boot(*[_cls(s) for s in P2_D], strict_caps=False)
    assert 'role="tree"' in _html(app, "tree")
    assert 'role="feed"' in _html(app, "feed")
    fab = _html(app, "fab")
    assert 'aria-controls="fab-menu"' in fab
    assert 'id="fab-menu"' in fab
    assert 'role="menu"' in fab
    assert 'hidden="hidden"' in fab
    resize = _html(app, "resizable")
    assert 'role="radiogroup"' in resize
    assert 'role="radio"' in resize
    assert "aria-checked" in resize
    kit = ROOT / "src" / "ux_compose" / "kit"
    for stem in P2_D:
        src = (kit / f"{stem}.py").read_text(encoding="utf-8")
        assert "ux_channel" not in src
        assert "cek_runtime" not in src


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_copy_p2_d(tmp_path: Path):
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    for stem in P2_D:
        written = copy_component(stem, root=tmp_path)
        ast.parse(written["py"].read_text(encoding="utf-8"))
