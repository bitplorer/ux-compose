"""InlineEdit — InlineEdit

Ported from the ``systems`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    App,
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    header,
    ul,
    li,
    span,
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty

class InlineEdit(Component):
    id = "inline"
    editing = MorphState(False)
    text = RefState("Work shirt")
    dirty = MorphState("idle")

    def render(self):
        if self.editing:
            body = form(
                field("text", str(self.text or "")),
                button("Save", type="submit", className="btn-primary", **control("inline.save")),
                method="post",
                action="/act/inline.save",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
        else:
            body = div(
                p(str(self.text or ""), className="lede"),
                act("inline.edit", "Edit", kind="ghost"),
            )
        kids = (
            header(
                p("Pencil / contenteditable stand-in", className="kicker"),
                h2("Inline edit", className="widget-title"),
            ),
            body,
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def edit(self):
        self.editing = True
        return update_with(self)

    @action(caps=())
    def save(self, text: str = ""):
        if text:
            self.text = text
        self.editing = False
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("saved")])


__all__ = ["InlineEdit"]
