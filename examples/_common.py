"""Shared helpers for full-length examples.

Canonical implementation: ``ux_compose.author``.
This module re-exports the same objects so existing example imports
(``from examples._common import act, mark_dirty, field, …``) stay one line.

``scene`` / ``rise`` / ``fade`` / ``slide`` are ux-motion (hard dependency).

Isolation Law: this module never imports ux_channel or CEK.
"""
from __future__ import annotations

from ux_compose import fade, rise, scene, slide
from ux_compose.author import (  # noqa: F401
    act,
    field,
    mark_dirty,
    fade_enter,
    rise_enter,
    slide_enter,
    status,
)

__all__ = [
    "mark_dirty",
    "rise_enter",
    "fade_enter",
    "slide_enter",
    "act",
    "field",
    "status",
    "scene",
    "rise",
    "fade",
    "slide",
]
