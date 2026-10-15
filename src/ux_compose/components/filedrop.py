"""FileDrop — Filenames in RefState. Count is derived. Upload-commit would take a Cap.

Ported from the ``fields`` example module (spec §4); that example stays as the teaching copy.
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

from ux_compose.author import act, field, mark_dirty, status

class FileDrop(Component):
    """Filenames in RefState. Count is derived. Upload-commit would take a Cap.

    Real bytes never live on the Component. Host owns the store.
    """

    id = "filedrop"
    files = RefState(())
    dirty = MorphState("idle")

    def render(self):
        rows = list(self.files or ())
        lis = [
            li(
                span(name, className="bag-line-name"),
                act("filedrop.remove", "Remove", kind="text", name=name),
                id=f"file-{i}",
                className="bag-line",
            )
            for i, name in enumerate(rows)
        ] or [li("Drop zone empty. Add a named stand-in.", className="muted")]
        kids = (
            header(
                p("Names in RefState · bytes on Host", className="kicker"),
                h2("File drop", className="widget-title"),
            ),
            p(f"{len(rows)} file(s). The Component never holds bytes.", className="lede"),
            ul(*lis, className="bag-lines"),
            div(
                act("filedrop.add", "Add linen.jpg", kind="secondary", name="linen.jpg"),
                act("filedrop.add", "Add oak.pdf", kind="secondary", name="oak.pdf"),
                act("filedrop.clear", "Clear", kind="text"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget file-drop")

    @action(caps=())
    def add(self, name: str = ""):
        name = (name or "").strip()
        if name and name not in (self.files or ()):
            self.files = tuple(self.files or ()) + (name,)
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(name)])

    @action(caps=())
    def remove(self, name: str = ""):
        self.files = tuple(x for x in (self.files or ()) if x != name)
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.files = ()
        mark_dirty(self)
        return update_with(self)


__all__ = ["FileDrop"]
