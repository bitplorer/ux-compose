"""Shared helpers for full-length examples.

Canonical implementation: ``ux_compose.author``.
This module re-exports the same objects so existing example imports
(``from examples._common import act, tick, field, …``) do not change.

``scene`` / ``rise`` / ``fade`` / ``slide`` stay as optional names
(None when ux-motion is absent). Dropping them broke Atelier imports.

Isolation Law: this module never imports ux_channel or CEK.
"""
from __future__ import annotations

from ux_compose.author import (  # noqa: F401
    act,
    field,
    maybe_fade,
    maybe_plan,
    maybe_slide,
    status,
    tick,
)

try:
    from ux_compose import fade, rise, scene
except Exception:  # pragma: no cover
    scene = rise = fade = None  # type: ignore
try:
    from ux_motion import slide  # type: ignore
except Exception:  # pragma: no cover
    slide = None  # type: ignore

__all__ = [
    "tick",
    "maybe_plan",
    "maybe_fade",
    "maybe_slide",
    "act",
    "field",
    "status",
]
