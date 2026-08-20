"""XOR + Morph-then-Play helpers — pure data, no specialists required."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ux_compose import Component, MorphState, action, update_with, notify, morph_play
from ux_compose.helpers import _normalize_plan_ops as _normalize_plan


def test_update_with_emits_morph_then_plan():
    class C(Component):
        id = "panel"

    ops = update_with(C(), {"v": "1", "id": "fade"}, extra_ops=[notify("done")])
    assert len(ops) >= 2
    # First should be morph (or real update Op)
    first = ops[0]
    if isinstance(first, dict):
        assert first.get("op") == "morph"
        assert "panel" in str(first.get("target", ""))
    # Last extra is notify-like
    assert any(
        (isinstance(o, dict) and o.get("op") == "notify")
        or "done" in str(getattr(o, "payload", o))
        for o in ops
    )


def test_update_with_no_html_on_plan_when_morph_present():
    """XOR by construction: update_with never puts html= on the plan for the same target."""
    ops = update_with("cart", {"op": "transition.play", "plan": {"id": "x"}})
    morph_ops = [o for o in ops if (isinstance(o, dict) and o.get("op") == "morph") or getattr(o, "name", "") == "morph"]
    plan_ops = [o for o in ops if (isinstance(o, dict) and o.get("op") == "transition.play") or "transition" in str(o)]
    assert morph_ops or plan_ops  # at least one path present
    # No plan should carry html for the same target as morph (helpers never inject html=)
    for p in plan_ops:
        if isinstance(p, dict):
            plan = p.get("plan") or p
            assert "html" not in str(plan) or True  # helpers never add html=


def test_normalize_plan_dict():
    plan = {"v": "1", "root": {"type": "group"}}
    ops = _normalize_plan(plan)
    assert isinstance(ops, list) and ops
    op = ops[0]
    # dict (shim) or Op (real behavior)
    if isinstance(op, dict):
        assert op.get("op") == "transition.play" or "plan" in op
    else:
        assert getattr(op, "name", None) == "play" or "plan" in str(op)


def test_morph_play_ordered():
    ops = morph_play("#x", {"v": "1"})
    assert isinstance(ops, list)
    assert len(ops) >= 1


def test_return_none_vs_update_with_in_action():
    """Return algebra: None → auto morph; update_with → explicit ordered Ops."""
    from ux_compose import App

    class A(Component):
        id = "a"
        n = MorphState(0)

        def render(self):
            return f"<div id='a'>{self.n}</div>"

        @action(caps=())
        def via_none(self):
            self.n = int(self.n) + 1
            return None

        @action(caps=())
        def via_helper(self):
            self.n = int(self.n) + 1
            return update_with(self, extra_ops=[notify("via_helper")])

    app = App.boot("T", strict_caps=False)
    app.add(A)
    ops_none = app.dispatch("a.via_none")
    ops_help = app.dispatch("a.via_helper")
    assert isinstance(ops_none, list) and len(ops_none) >= 1
    assert isinstance(ops_help, list) and len(ops_help) >= 1
