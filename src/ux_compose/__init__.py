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
    "__version__",
]
