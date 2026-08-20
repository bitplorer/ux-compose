"""Real HTML morph patches — render() output flows into update() Op."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

HAS_BEHAVIOR = importlib.util.find_spec("ux_behavior") is not None
HAS_DOM = importlib.util.find_spec("ux_dom") is not None


def test_update_with_includes_render_html():
    from ux_compose import Component, MorphState, update_with

    class Box(Component):
        id = "box"
        n = MorphState(0)

        def render(self):
            return f'<div id="box" data-n="{self.n}">n={self.n}</div>'

    inst = Box()
    inst.n = 3
    ops = update_with(inst)
    assert ops
    first = ops[0]
    payload = getattr(first, "payload", None) or first
    patch = ""
    if isinstance(payload, dict):
        patch = str(payload.get("patch") or payload.get("html") or "")
    else:
        patch = str(first)
    assert "n=3" in patch or "data-n=\"3\"" in patch or "3" in patch


@pytest.mark.skipif(not HAS_BEHAVIOR, reason="ux-behavior required")
def test_dispatch_morph_carries_html():
    from ux_compose import App, Component, MorphState, action, update_with, notify

    class Cart(Component):
        id = "cart"
        count = MorphState(0)

        def render(self):
            return f'<div id="cart">count={self.count}</div>'

        @action(caps=())
        def add(self):
            self.count = int(self.count) + 1
            return update_with(self, extra_ops=[notify("ok")])

    app = App.boot("S", strict_caps=False)
    app.add(Cart)
    ops = app.dispatch("cart.add")
    assert ops
    morph = ops[0]
    payload = getattr(morph, "payload", {}) or {}
    patch = str(payload.get("patch") or "")
    assert "count=1" in patch


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom required for tree morph")
def test_ux_dom_tree_serializes_via_render_pretty_false():
    from ux_compose.helpers import _serialize_tree, update_with
    from ux_compose import Component, MorphState
    from ux_dom.dom import div, span

    class Card(Component):
        id = "card"
        n = MorphState(2)

        def render(self):
            return div(span(f"n={self.n}"), id=self.id, className="card")

    inst = Card()
    tree = inst.render()
    compact = _serialize_tree(tree)
    pretty = str(tree)
    assert "n=2" in compact
    assert 'id="card"' in compact or "id='card'" in compact
    # pretty=False is denser (no indent noise) — at minimum it is real HTML
    assert "<div" in compact and "</div>" in compact
    ops = update_with(inst)
    payload = getattr(ops[0], "payload", None) or ops[0]
    patch = str(payload.get("patch") or payload.get("html") or "")
    assert "n=2" in patch
    # Morph patch must not be the Python repr of the tag
    assert "dom_tag" not in patch
    assert "HTMLElement" not in patch
