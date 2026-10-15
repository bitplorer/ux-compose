"""Control argument names become HTML attribute names.

A name that is not an identifier can close the attribute early
(``data-ux-arg-x" onclick="alert(1)"``). Values stay caller data;
the serializer escapes those. Names are rejected.
"""
from __future__ import annotations

import pytest

from ux_compose.helpers import bind, control

_BREAKOUT = {'x" onclick="alert(1)': "z"}


def test_control_rejects_attribute_name_breakout():
    with pytest.raises(ValueError, match="attribute name"):
        control("add", **_BREAKOUT)


def test_bind_string_rejects_attribute_name_breakout():
    with pytest.raises(ValueError, match="attribute name"):
        bind("cart.add", **_BREAKOUT)


def test_bind_callable_with_var_keyword_rejects_attribute_name_breakout():
    from ux_compose import action

    class Box:
        @action
        def add(self, **kwargs):
            return []

    with pytest.raises(ValueError, match="attribute name"):
        bind(Box().add, **_BREAKOUT)


def test_control_rejects_non_identifier_names():
    with pytest.raises(ValueError, match="attribute name"):
        control("add", **{"item-id": "1"})
    with pytest.raises(ValueError, match="attribute name"):
        control("add", **{"x y": "1"})
    with pytest.raises(ValueError, match="attribute name"):
        control("add", **{"": "1"})


def test_control_keeps_identifier_names_and_raw_values():
    """Characterization: this passed on #102 before attribute-name rejection."""
    attrs = control("add", sku='a"b<c')
    assert attrs["data-ux-arg-sku"] == 'a"b<c'
    assert "data-ux-action" in attrs
    assert "onclick" not in "".join(attrs)


def test_live_control_attrs_rejects_attribute_name_breakout():
    from ux_compose.wire.caps import control_attrs

    class _Mint:
        def mint(self, action, args):
            return "tok"

    with pytest.raises(ValueError, match="attribute name"):
        control_attrs(_Mint(), "add", **_BREAKOUT)
