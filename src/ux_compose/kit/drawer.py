"""Drawer is a Sheet alias — same Host, right-edge panel.

Not a second Host. ``kind=drawer`` on OverlayChrome maps to the same
right edge as Sheet. MorphState / Caps / a11y: see ``Sheet``.

Copied by ``uxcompose add drawer`` also lands ``sheet.py`` (sibling rewrite).
"""

from __future__ import annotations

from ux_compose.kit.sheet import Sheet as Drawer

__all__ = ["Drawer"]
