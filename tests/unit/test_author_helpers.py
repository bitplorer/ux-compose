"""Author helpers are the public form of examples/_common — same objects."""
from __future__ import annotations

from ux_compose.author import act, field, status, tick


class _Stamp:
    stamp = "tick"


def test_tick_flips_qualitative_stamp():
    comp = _Stamp()
    tick(comp)
    assert comp.stamp == "tock"
    tick(comp)
    assert comp.stamp == "tick"


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
