"""RED spec — visible placeholders (docs/specs/component-params-placeholders.md §3).

A component used without its required data renders a placeholder that names the
component and the missing params. Mode: "show" (dev), "hide" (no names leak),
"raise" (strict). GUARD tests already pass on main.
"""
from __future__ import annotations

import warnings

import pytest

from ux_compose import Component, div, h2


class Greeting(Component):
    id = "greeting"

    def render(self, *, title: str, subtitle: str, count: int = 0):
        return div(h2(title), subtitle, id=self.id)


def test_placeholder_module_exists():
    from ux_compose import placeholder  # noqa: F401


def test_show_mode_names_component_and_missing_params():
    from ux_compose.placeholder import use_placeholder_mode

    with use_placeholder_mode("show"):
        out = Greeting().__render__()
    assert 'data-ux-placeholder="Greeting"' in out
    assert 'data-ux-missing="subtitle,title"' in out
    assert "count" not in out  # has a default, not missing


def test_show_mode_is_accessible_and_keeps_morph_target():
    from ux_compose.placeholder import use_placeholder_mode

    with use_placeholder_mode("show"):
        out = Greeting().__render__()
    assert 'role="note"' in out
    assert 'aria-label="Greeting placeholder: missing subtitle, title"' in out
    assert 'id="greeting"' in out


def test_partial_data_lists_only_missing():
    from ux_compose.placeholder import use_placeholder_mode

    with use_placeholder_mode("show"):
        out = Greeting(title="T").__render__()
    assert 'data-ux-missing="subtitle"' in out


def test_hide_mode_leaks_no_names_but_warns():
    from ux_compose.placeholder import MissingParamsWarning, use_placeholder_mode

    with use_placeholder_mode("hide"), warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        out = Greeting().__render__()
    assert "data-ux-placeholder" not in out and "subtitle" not in out
    assert 'id="greeting"' in out and "hidden" in out
    assert any(issubclass(x.category, MissingParamsWarning) for x in w)


def test_raise_mode_raises_missing_params():
    from ux_compose.placeholder import MissingParams, use_placeholder_mode

    with use_placeholder_mode("raise"), pytest.raises(MissingParams) as ei:
        Greeting().__render__()
    assert issubclass(MissingParams, TypeError)
    assert "Greeting" in str(ei.value) and "title" in str(ei.value)


def test_default_mode_is_hide_outside_dev():
    from ux_compose.placeholder import placeholder_mode

    assert placeholder_mode() == "hide"


def test_kit_uses_same_placeholder_helper():
    from ux_compose.kit import Badge
    from ux_compose.placeholder import placeholder_for

    out = str(placeholder_for(Badge(), missing=("items",)))
    assert 'data-ux-placeholder="Badge"' in out and 'data-ux-missing="items"' in out


def test_complete_component_renders_no_placeholder():  # GUARD
    class Done(Component):
        id = "done"

        def render(self):
            return div("ok", id=self.id)

    assert "data-ux-placeholder" not in Done().__render__()


def test_every_catalog_pattern_renders_without_placeholder():  # GUARD
    from examples.catalog import all_components

    for cls in all_components():
        assert "data-ux-placeholder" not in cls().__render__(), cls.__name__
