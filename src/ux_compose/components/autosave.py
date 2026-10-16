"""Autosave — Unsaved MorphState. Draft body RefState. Saved is a name.

Ported from the ``fields`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
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
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty

class Autosave(Component):
    """Unsaved MorphState. Draft body RefState. Saved is a name.

    Debounce lives on the Host. Behavior only holds the window.
    """

    id = "autosave"
    unsaved = MorphState(False)
    draft = RefState("Quiet pieces for a working house.")
    saved = MorphState("clean")
    dirty = MorphState("idle")

    def render(self):
        kids = (
            header(
                p("Unsaved flag · draft silent", className="kicker"),
                h2("Autosave", className="widget-title"),
            ),
            p(str(self.draft or ""), className="lede"),
            p(
                "Unsaved changes." if self.unsaved else f"Saved · {self.saved}.",
                className="muted",
            ),
            form(
                field("text", str(self.draft or ""), placeholder="Draft"),
                button("Type", type="submit", className="btn-secondary", **control("autosave.type")),
                method="post",
                action="/act/autosave.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ),

            div(
                act("autosave.type", "Edit a line", kind="ghost", text="Held until you place."),
                act("autosave.save", "Save now", kind="primary"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget", data_unsaved="1" if self.unsaved else "0")

    @action(caps=())
    def type(self, text: str = ""):
        if text:
            self.draft = text
        self.unsaved = True
        self.saved = "unsaved"
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def save(self):
        self.unsaved = False
        self.saved = "just-now"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("saved")])


__all__ = ["Autosave"]
