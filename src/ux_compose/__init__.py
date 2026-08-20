"""
ux-compose — pure-Python composition root for ux-dom + ux-behavior + ux-motion + ux-channel.

Cold import never pulls the wire. Isolation Law enforced.
"""

from __future__ import annotations

__version__ = "0.1.0"

# Core author surface (Level 1+)
from ux_compose.component import Component, MorphState, RefState, action
from ux_compose.helpers import control, notify, update_with, morph_play
from ux_compose.app import App
from ux_compose.progressive import Level
from ux_compose.doctor import doctor, DoctorResult

# Motion helpers re-exported only if available; never pull channel
try:
    from ux_motion import scene, fade, rise  # type: ignore
except ImportError:  # pragma: no cover
    scene = fade = rise = None  # type: ignore

# ux-dom tags — first-class render() return type when the specialist is present
from ux_compose.dom import (  # noqa: E402
    HAS_DOM,
    a,
    article,
    aside,
    button,
    circle,
    div,
    footer,
    form,
    h1,
    h2,
    h3,
    header,
    input_,
    label,
    li,
    main,
    nav,
    p,
    path,
    rect,
    section,
    span,
    svg,
    ul,
)

__all__ = [
    "App",
    "Component",
    "MorphState",
    "RefState",
    "action",
    "control",
    "notify",
    "update_with",
    "morph_play",
    "Level",
    "doctor",
    "DoctorResult",
    "scene",
    "fade",
    "rise",
    "HAS_DOM",
    "div",
    "span",
    "h1",
    "h2",
    "h3",
    "p",
    "a",
    "button",
    "form",
    "input_",
    "ul",
    "li",
    "header",
    "footer",
    "aside",
    "section",
    "article",
    "nav",
    "main",
    "label",
    "svg",
    "path",
    "rect",
    "circle",
    "__version__",
]
