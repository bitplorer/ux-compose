"""
ux-compose — pure-Python composition root for ux-dom + ux-behavior + ux-motion + ux-channel.

Cold import never pulls the wire. Isolation Law enforced.

Public author surface is this package root. See docs/ARCHITECTURE.md.
"""

from __future__ import annotations

__version__ = "0.1.0"

from ux_compose.component import Component, MorphState, RefState, action
from ux_compose.helpers import bind, control, notify, update_with, morph_play
from ux_compose.app import App
from ux_compose.surfaces import (
    Surface,
    SurfaceBundle,
    SurfaceError,
    mount_surfaces,
    scan_surfaces,
    validate_surfaces,
)
from ux_compose.progressive import Level
from ux_compose.doctor import doctor, DoctorResult
from ux_compose.build import build
from ux_compose.assets import WebAssets
from ux_compose.routing import DirectoryASGI, DirectoryRoutes, RouterHooks
from ux_compose.author import (
    act,
    field,
    maybe_fade,
    maybe_plan,
    maybe_slide,
    status,
    tick,
)
from ux_compose.attach_notes import AttachNote, attach_notes

try:
    from ux_motion import scene, fade, rise, slide  # type: ignore
except ImportError:  # pragma: no cover
    scene = fade = rise = slide = None  # type: ignore

from ux_compose.dom import (  # noqa: E402
    HAS_DOM,
    a,
    article,
    aside,
    body,
    button,
    circle,
    div,
    footer,
    form,
    h1,
    h2,
    h3,
    head,
    header,
    html,
    input_,
    label,
    li,
    link,
    main,
    meta,
    nav,
    p,
    path,
    raw,
    rect,
    script,
    section,
    span,
    style,
    svg,
    title,
    ul,
)

__all__ = [
    "App",
    "build",
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
    "Component",
    "MorphState",
    "RefState",
    "action",
    "bind",
    "control",
    "notify",
    "update_with",
    "morph_play",
    "act",
    "tick",
    "field",
    "status",
    "maybe_plan",
    "maybe_fade",
    "maybe_slide",
    "AttachNote",
    "attach_notes",
    "Level",
    "doctor",
    "DoctorResult",
    "scene",
    "fade",
    "rise",
    "slide",
    "HAS_DOM",
    "raw",
    "html",
    "head",
    "body",
    "title",
    "style",
    "meta",
    "link",
    "script",
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
