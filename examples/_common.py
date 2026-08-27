"""Shared helpers for full-length examples.

Isolation Law: this module never imports ux_channel
or ux-motion directly for control-plane work — only optional Plan builders
when Motion is installed.

``act()`` emits a progressive form: hidden fields + submit. The studio host
posts ``application/x-www-form-urlencoded`` (not multipart FormData) so
Behavior never sees a WebKit boundary as a kwarg.
"""
from __future__ import annotations

from typing import Any, Optional

from ux_compose import (
    HAS_DOM,
    button,
    control,
    form,
    input_,
    span,
)

try:
    from ux_compose import scene, rise, fade
except Exception:  # pragma: no cover
    scene = rise = fade = None
try:
    from ux_motion import slide
except Exception:  # pragma: no cover
    slide = None


def tick(comp: Any, *, on: str = "tick", off: str = "tock") -> None:
    """Flip a qualitative MorphState stamp so RefState-only mutations morph."""
    cur = str(getattr(comp, "stamp", "") or "")
    setattr(comp, "stamp", off if cur == on else on)


def maybe_plan(name: str, target: str, *, ms: int = 140):
    """Build a rise-enter Plan when Motion is installed; else None.

    XOR: the Plan carries recipes only — never html=. Morph HTML comes from
    ``update_with(component)`` which serializes live ``render()``.
    """
    if scene is None or rise is None:
        return None
    try:
        return scene(name).enter(target, rise.enter(ms=ms))
    except Exception:
        return None


def maybe_fade(name: str, target: str, *, ms: int = 120):
    if scene is None or fade is None:
        return None
    try:
        return scene(name).enter(target, fade.enter(ms=ms))
    except Exception:
        return None


def maybe_slide(name: str, target: str, *, direction: str = "next", ms: int = 180):
    if scene is None or slide is None:
        return None
    try:
        from ux_motion import tokens as _tok
        dist = float(_tok.dist("md"))
    except Exception:
        dist = 24.0
    x = -dist if direction == "prev" else dist
    try:
        return scene(name).enter(target, slide.enter(x=x, ms=ms))
    except Exception:
        return None
