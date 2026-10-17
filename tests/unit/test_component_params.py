"""RED spec — component parameters (docs/specs/component-params-placeholders.md §2).

Pattern (uidom, bitplorer/uidom uidom/dom/src/component.py:47-54): the call
site's args go to ``render`` like a normal Python function. ux-compose re-runs
``render()`` on every morph, so the constructor *binds* the call-site args
against ``render``'s signature and replays them on each render.

Tests marked GUARD already pass on main and must stay green.
"""
from __future__ import annotations

import pytest

from ux_compose import Component, div, h2, p
from ux_compose.helpers import _serialize_tree


class Greeting(Component):
    id = "greeting"

    def render(self, *, title: str, count: int = 0):
        return div(h2(title), p(str(count)), id=self.id)


def html(c) -> str:
    return c.__render__()


def test_ctor_kwargs_reach_render_like_function_args():
    assert "Hello" in html(Greeting(title="Hello"))


def test_default_param_used_when_omitted():
    out = "".join(html(Greeting(title="Hi")).split())  # serializer pretty-prints
    assert "<p>0</p>" in out


def test_params_survive_rerender():
    g = Greeting(title="Stay", count=3)
    assert html(g) == html(g)
    assert "Stay" in html(g) and "3" in html(g)


def test_instances_are_isolated():
    a, b = Greeting(title="A"), Greeting(title="B")
    assert "A" in html(a) and "B" in html(b) and "B" not in html(a)


def test_unknown_param_raises_typeerror_naming_component():
    with pytest.raises(TypeError) as ei:
        Greeting(title="x", bogus=1)
    msg = str(ei.value)
    assert "Greeting" in msg and "bogus" in msg


def test_explicit_render_args_override_bound_params():
    g = Greeting(title="Bound")
    assert "Override" in _serialize_tree(g.render(title="Override"))


def test_zero_arg_component_still_constructs():  # GUARD
    class Plain(Component):
        id = "plain"

        def render(self):
            return div("plain", id=self.id)

    assert "plain" in html(Plain())


def test_kit_render_slots_backcompat():  # GUARD
    from ux_compose.kit import Badge

    assert "Alpha" in _serialize_tree(Badge().render(items=(("a", "Alpha"),), shell=False))


def test_kit_ctor_kwargs_equal_render_slots():
    from ux_compose.kit import Badge

    via_ctor = html(Badge(items=(("a", "Alpha"),), shell=False))
    via_slot = _serialize_tree(Badge().render(items=(("a", "Alpha"),), shell=False))
    assert via_ctor == via_slot
