"""Shared helpers for full-length examples.

Canonical implementation: ``ux_compose.author``.
This module re-exports the same objects so existing example imports
(``from examples._common import act, tick, field, …``) do not change.

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

__all__ = [
    "tick",
    "maybe_plan",
    "maybe_fade",
    "maybe_slide",
    "act",
    "field",
    "status",
]
