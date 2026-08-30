"""Shared overlay chrome — ids, edge, swipe-on-dismiss, open plan.

Dialog / Sheet / ActionSheet take ids, dismiss grammar, and open plan
from this primitive. Markup and Tailwind stay on the widget. The defect
this exists to stop is copy-pasted scrim/panel/dismiss ids plus a root
swipe token that swallows row clicks.

Isolation Law: this module never imports ux_channel or CEK.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional


KIND_EDGE = {
    "modal": "center",
    "dialog": "center",
    "sheet": "right",
    "drawer": "right",
    "action": "bottom",
    "actionsheet": "bottom",
}

EDGE_SWIPE = {
    "center": "click swipe.down",
    "right": "click swipe.right",
    "left": "click swipe.left",
    "bottom": "click swipe.down",
    "top": "click swipe.up",
}

# Handle (ActionSheet) adds vertical so row clicks survive. Dismiss does not.
HANDLE_SWIPE = {
    "bottom": "click swipe.down swipe.vertical threshold:48",
    "top": "click swipe.up swipe.vertical threshold:48",
}

# Shipped enter distances. Right sheet x=28; bottom actionsheet y=32.
EDGE_SLIDE = {
    "right": {"x": 28.0},
    "left": {"x": -28.0},
    "bottom": {"y": 32.0},
    "top": {"y": -32.0},
}


def _edge_for(kind: str, root_id: str) -> str:
    key = (kind or root_id or "modal").lower().strip()
    return KIND_EDGE.get(key, "center")


@dataclass(frozen=True)
class OverlayChrome:
    """Stable overlay ids + dismiss grammar. Not a widget.

    ``open_plan()`` is selectors-only (no ``html=``). Close stays morph-only:
    after apply the panel is gone, so an exit recipe in the same Result has
    nothing to play.
    """

    root_id: str
    kind: str = "modal"
    edge: str = "center"

    @property
    def scrim_id(self) -> str:
        return f"{self.root_id}-scrim"

    @property
    def panel_id(self) -> str:
        return f"{self.root_id}-panel"

    @property
    def dismiss_id(self) -> str:
        return f"{self.root_id}-dismiss"

    def swipe_on_dismiss(self) -> str:
        """Channel grammar for the dismiss control — never the root.

        Root ``swipe.*`` swallows row clicks (ActionSheet / Sheet defect).
        Dismiss keeps ``click`` so a tap still works without a finger swipe.
        """
        return EDGE_SWIPE.get(self.edge, "click swipe.down")

    def swipe_on_handle(self) -> str:
        """Handle grammar. Bottom sheets add vertical so row clicks survive."""
        return HANDLE_SWIPE.get(self.edge, self.swipe_on_dismiss())

    def open_plan(self, *, fade_ms: int = 120, enter_ms: int = 180) -> Any:
        """Motion enter plan, or None when ux-motion is absent."""
        try:
            from ux_motion import scene, fade, rise, slide  # type: ignore
        except Exception:
            return None
        if scene is None or fade is None:
            return None
        try:
            plan = scene(f"{self.root_id}-open").enter(
                f"#{self.scrim_id}", fade.enter(ms=fade_ms)
            )
            if self.edge == "center" and rise is not None:
                return plan.enter(f"#{self.panel_id}", rise.enter(ms=enter_ms))
            if slide is not None:
                delta = EDGE_SLIDE.get(self.edge) or {}
                x = float(delta.get("x", 0.0))
                y = float(delta.get("y", 0.0))
                if y:
                    return plan.enter(
                        f"#{self.panel_id}", slide.enter(x=x, y=y, ms=enter_ms)
                    )
                return plan.enter(f"#{self.panel_id}", slide.enter(x=x, ms=enter_ms))
            if rise is not None:
                return plan.enter(f"#{self.panel_id}", rise.enter(ms=enter_ms))
            return plan
        except Exception:
            return None


def overlay(root_id: str, *, kind: Optional[str] = None, edge: Optional[str] = None) -> OverlayChrome:
    """Factory. ``kind`` picks the default edge when ``edge`` is omitted."""
    resolved_kind = (kind or root_id or "modal").lower().strip()
    resolved_edge = edge or _edge_for(resolved_kind, root_id)
    return OverlayChrome(root_id=root_id, kind=resolved_kind, edge=resolved_edge)


__all__ = ["OverlayChrome", "overlay"]
