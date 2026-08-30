"""Capability baseline: public names are only added, never removed."""
from __future__ import annotations

import ux_compose as ux


REQUIRED = {
    "App",
    "Component",
    "MorphState",
    "RefState",
    "action",
    "bind",
    "control",
    "notify",
    "update_with",
    "morph_play",
    "build",
    "doctor",
    "Level",
}


ADDED = {
    "act",
    "tick",
    "field",
    "status",
    "maybe_plan",
    "maybe_fade",
    "maybe_slide",
    "DegradeEvent",
    "degrades",
}


def test_required_public_names_still_exported():
    missing = REQUIRED - set(ux.__all__)
    assert not missing, missing
    for name in REQUIRED:
        assert getattr(ux, name) is not None


def test_author_helpers_are_public_and_match_common():
    missing = ADDED - set(ux.__all__)
    assert not missing, missing
    from examples._common import act as common_act, tick as common_tick

    assert ux.act is common_act
    assert ux.tick is common_tick


def test_common_keeps_scene_rise_names():
    """Atelier examples import scene/rise from _common. None is a legal degrade."""
    from examples import _common

    assert hasattr(_common, "scene")
    assert hasattr(_common, "rise")
    assert hasattr(_common, "fade")
    assert hasattr(_common, "slide")
