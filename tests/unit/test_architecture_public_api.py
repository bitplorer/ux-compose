"""Capability baseline: required names stay; nomen-cut helpers replace maybe_*/tick."""
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
    "mark_dirty",
    "field",
    "status",
    "optional_plan",
    "optional_fade",
    "optional_slide",
    "AttachNote",
    "attach_notes",
}


HOST = {
    "WebAssets",
    "DirectoryRoutes",
    "DirectoryASGI",
    "RouterHooks",
    "Surface",
    "SurfaceBundle",
    "SurfaceError",
    "mount_surfaces",
    "scan_surfaces",
    "validate_surfaces",
    "DoctorResult",
    "scene",
    "fade",
    "rise",
    "slide",
}


def test_required_public_names_still_exported():
    missing = REQUIRED - set(ux.__all__)
    assert not missing, missing
    for name in REQUIRED:
        assert getattr(ux, name) is not None


def test_author_helpers_are_public_and_match_common():
    missing = ADDED - set(ux.__all__)
    assert not missing, missing
    from examples._common import act as common_act, mark_dirty as common_mark_dirty

    assert ux.act is common_act
    assert ux.mark_dirty is common_mark_dirty


def test_host_surface_motion_names_still_exported():
    missing = HOST - set(ux.__all__)
    assert not missing, missing
    for name in HOST:
        assert getattr(ux, name) is not None


def test_nomen_cut_drops_maybe_and_tick_names():
    leftover = {"tick", "maybe_plan", "maybe_fade", "maybe_slide"} & set(ux.__all__)
    assert not leftover, leftover


def test_common_keeps_scene_rise_names():
    from examples import _common

    assert hasattr(_common, "scene")
    assert hasattr(_common, "rise")
    assert hasattr(_common, "fade")
    assert hasattr(_common, "slide")
