"""Author helpers are the public form of examples/_common — same objects."""
from __future__ import annotations

from ux_compose.author import act, field, mark_dirty, status


class _Dirty:
    dirty = "tick"


def test_mark_dirty_flips_qualitative_dirty():
    comp = _Dirty()
    mark_dirty(comp)
    assert comp.dirty == "tock"
    mark_dirty(comp)
    assert comp.dirty == "tick"


def test_act_string_fallback_has_action_and_hidden():
    html = act("cart.add", "+ tee", sku="tee")
    text = html if isinstance(html, str) else str(html)
    assert "/act/cart.add" in text
    assert "tee" in text


def test_field_and_status_offline_strings():
    f = field("q", value="oak", placeholder="search")
    s = status("saved", kind="ok")
    ft = f if isinstance(f, str) else str(f)
    st = s if isinstance(s, str) else str(s)
    assert "oak" in ft
    assert "saved" in st


def test_stepper_finish_cap_is_stepper_finish():
    from ux_compose.kit.stepper import Stepper

    caps = tuple(getattr(Stepper.finish, "_ux_behavior_caps", ()) or getattr(Stepper.finish, "_ux_caps", ()) or ())
    assert caps == ("stepper.finish",)
    assert "flow.finish" not in caps
