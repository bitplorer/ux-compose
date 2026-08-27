"""ux-compose — pure-Python composition for progressive HTML."""

from __future__ import annotations

__version__ = "0.1.0"

from ux_compose.component import Component, MorphState, RefState, action
from ux_compose.app import App
from ux_compose.helpers import update_with, notify, control, bind
from ux_compose.dom import (
    HAS_DOM,
    div,
    span,
    p,
    h1,
    h2,
    h3,
    button,
    form,
    input_,
    label,
    section,
    header,
    footer,
    nav,
    ul,
    li,
    a,
    img,
    table,
    thead,
    tbody,
    tr,
    th,
    td,
)

try:
    from ux_motion import scene, fade, rise, slide  # type: ignore
except ImportError:  # pragma: no cover
    scene = fade = rise = slide = None  # type: ignore

__all__ = [
    "Component",
    "MorphState",
    "RefState",
    "action",
    "App",
    "update_with",
    "notify",
    "control",
    "bind",
    "HAS_DOM",
    "div",
    "span",
    "p",
    "h1",
    "h2",
    "h3",
    "button",
    "form",
    "input_",
    "label",
    "section",
    "header",
    "footer",
    "nav",
    "ul",
    "li",
    "a",
    "img",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "scene",
    "fade",
    "rise",
    "slide",
    "__version__",
]
