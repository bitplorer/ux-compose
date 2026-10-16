"""Lightbox — Lightbox

Ported from the ``overlays`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    update_with,
    div,
    h2,
    p,
    header,
)

from ux_compose.author import act, mark_dirty, optional_plan, optional_slide, optional_fade

class Lightbox(Component):
    id = "lightbox"
    open = MorphState(False)
    index = RefState(0)
    dirty = MorphState("idle")
    SLIDES = ("Linen in raking light", "Oak end-grain", "Wool nap", "Clay lip")

    def render(self):
        i = int(self.index or 0) % len(self.SLIDES)
        if self.open:
            stage = div(
                p(self.SLIDES[i], className="slide-copy"),
                div(
                    act("lightbox.prev", "Prev", kind="ghost", on="click swipe.right"),
                    act("lightbox.next", "Next", kind="ghost", on="click swipe.left"),
                    act("lightbox.close", "Close", kind="text"),
                    className="row-actions",
                ),
                className="slide",
                id=f"slide-{i}",
                style="touch-action:pan-y;user-select:none;",
            )
        else:
            stage = act("lightbox.open_box", "Open viewer", kind="primary", index="0")
        kids = (
            header(
                p("Swipe when open · Index is RefState", className="kicker"),
                h2("Lightbox", className="widget-title"),
            ),
            stage,
        )
        attrs = {"id": self.id, "className": "widget"}
        if self.open:
            attrs["data_channel_on"] = "swipe.horizontal threshold:48"
        return div(*kids, **attrs)

    @action(caps=())
    def open_box(self, index: str = "0"):
        self.open = True
        self.index = int(index or 0)
        mark_dirty(self)
        return update_with(self, optional_plan("lb-open", f"#{self.id}", ms=140))

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self, optional_fade("lb-close", f"#{self.id}", ms=100))

    @action(caps=())
    def next(self):
        self.index = (int(self.index or 0) + 1) % len(self.SLIDES)
        mark_dirty(self)
        return update_with(
            self, optional_slide("lb-next", f"#{self.id}", direction="next", ms=160)
        )

    @action(caps=())
    def prev(self):
        self.index = (int(self.index or 0) - 1) % len(self.SLIDES)
        mark_dirty(self)
        return update_with(
            self, optional_slide("lb-prev", f"#{self.id}", direction="prev", ms=160)
        )


__all__ = ["Lightbox"]
