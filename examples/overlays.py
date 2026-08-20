"""Overlays — Toasts, Confirm, Lightbox, Command palette, Banner.

Overlays are Components with an open/items MorphState, not a second Document.
Document SSoT still holds: one HTML shell, many units.

Confirm's destructive verb is Cap-protected. Opening the dialog is public.

Run:
  PYTHONPATH=src:. python examples/overlays.py
"""
from __future__ import annotations

from ux_compose import (
    HAS_DOM,
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
)

from examples._common import act, tick, maybe_plan


class Toasts(Component):
    """Stack of one-shot messages. Push is public. Items live in RefState."""

    id = "toasts"
    items = RefState(())
    stamp = MorphState("idle")
    _seq = RefState(0)

    def render(self):
        rows = list(self.items or ())
        lis = [
            li(str(row.get("message", "")), id=f"toast-{row.get('id')}", className="toast")
            for row in rows[-4:]
        ]
        kids = (
            header(
                p("notify() is the Op. This unit *shows* them.", className="kicker"),
                h2("Toasts", className="widget-title"),
            ),
            ul(*lis, className="toast-list") if lis else p("None yet.", className="muted"),
            div(
                act("toasts.push", "Push note", kind="primary", message="Saved to the table"),
                act("toasts.clear", "Clear", kind="ghost"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def push(self, message: str = "Saved"):
        self._seq = int(self._seq or 0) + 1
        row = {"id": str(self._seq), "message": message}
        self.items = tuple(self.items or ()) + (row,)
        tick(self)
        return update_with(
            self,
            maybe_plan("toast-in", f"#toast-{row['id']}", ms=100),
            extra_ops=[notify(message)],
        )

    @action(caps=())
    def clear(self):
        self.items = ()
        tick(self)
        return update_with(self)


class Confirm(Component):
    """Ask, then Cap-protected confirm. Target id is silent RefState."""

    id = "confirm"
    open = MorphState(False)
    target = RefState("")

    def render(self):
        if not self.open:
            kids = (
                header(
                    p("Public ask · protected confirm", className="kicker"),
                    h2("Confirm", className="widget-title"),
                ),
                p("Destroying a row is an authority event.", className="lede"),
                act("confirm.ask", "Delete the oak board…", kind="secondary", id="oak-02"),
            )
            if HAS_DOM:
                return div(*kids, id=self.id, className="widget", data_open="0")
            return f'<div id="{self.id}" hidden></div>'
        kids = (
            header(h2("Delete this piece?")),
            p(f"Target {self.target or 'row'}. This cannot be undone.", className="lede"),
            div(
                act("confirm.cancel", "Keep it", kind="ghost"),
                act("confirm.confirm", "Delete", kind="primary"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(
                *kids,
                id=self.id,
                className="widget dialog",
                role="dialog",
                data_open="1",
            )
        return f'<div id="{self.id}" role="dialog"></div>'

    @action(caps=())
    def ask(self, id: str = ""):
        self.target = id
        self.open = True
        return update_with(self)

    @action(caps=())
    def cancel(self):
        self.open = False
        self.target = ""
        return update_with(self)

    @action(caps=("items.delete",))
    def confirm(self):
        gone = self.target
        self.open = False
        self.target = ""
        return update_with(self, extra_ops=[notify(f"deleted {gone}")])


class Lightbox(Component):
    id = "lightbox"
    open = MorphState(False)
    index = RefState(0)
    stamp = MorphState("idle")
    SLIDES = ("Linen in raking light", "Oak end-grain", "Wool nap", "Clay lip")

    def render(self):
        i = int(self.index or 0) % len(self.SLIDES)
        stage = (
            div(
                p(self.SLIDES[i], className="slide-copy"),
                div(
                    act("lightbox.prev", "Prev", kind="ghost"),
                    act("lightbox.next", "Next", kind="ghost"),
                    act("lightbox.close", "Close", kind="text"),
                    className="row-actions",
                ),
                className="slide",
                id=f"slide-{i}",
            )
            if self.open
            else act("lightbox.open_box", "Open viewer", kind="primary", index="0")
        )
        kids = (
            header(
                p("Index is RefState", className="kicker"),
                h2("Lightbox", className="widget-title"),
            ),
            stage,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def open_box(self, index: str = "0"):
        self.open = True
        self.index = int(index or 0)
        tick(self)
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=())
    def next(self):
        self.index = (int(self.index or 0) + 1) % len(self.SLIDES)
        tick(self)
        return update_with(self)

    @action(caps=())
    def prev(self):
        self.index = (int(self.index or 0) - 1) % len(self.SLIDES)
        tick(self)
        return update_with(self)


class Palette(Component):
    """Command palette. Query is MorphState (must repaint matches)."""

    id = "palette"
    open = MorphState(False)
    query = MorphState("")
    COMMANDS = (
        ("counter.inc", "Increase the counter"),
        ("tabs.select", "Open the Make tab"),
        ("drawer.open_drawer", "Open filters"),
        ("toasts.push", "Push a toast"),
    )

    def render(self):
        q = str(self.query or "").lower()
        hits = [(a, lab) for a, lab in self.COMMANDS if q in lab.lower() or q in a]
        rows = [
            li(act(a, lab, kind="text"), className="palette-row", id=f"cmd-{i}")
            for i, (a, lab) in enumerate(hits[:6])
        ]
        finder = (
            div(
                act("palette.close", "Close", kind="text"),
                p(f"Filter: {q or 'all'}", className="muted"),
                div(
                    act("palette.type", "All", kind="ghost", q=""),
                    act("palette.type", "Toast", kind="ghost", q="toast"),
                    act("palette.type", "Tab", kind="ghost", q="tab"),
                    className="row-actions",
                ),
                ul(*rows, className="palette-list") if rows else p("No matches.", className="muted"),
                className="palette-panel",
            )
            if self.open
            else act("palette.open_pal", "Open palette", kind="primary")
        )
        kids = (
            header(
                p("Query MorphState", className="kicker"),
                h2("Command palette", className="widget-title"),
            ),
            finder,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def open_pal(self):
        self.open = True
        self.query = ""
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        return update_with(self)


class Banner(Component):
    id = "banner"
    hidden = MorphState(False)

    def render(self):
        if self.hidden:
            kids = (
                header(h2("Banner")),
                p("Dismissed. Refresh of MorphState is the whole story.", className="muted"),
                act("banner.show", "Restore", kind="ghost"),
            )
        else:
            kids = (
                header(
                    p("Announcement", className="kicker"),
                    h2("Table of the week is live", className="widget-title"),
                ),
                p("A one-shot flag. Not a second Document.", className="lede"),
                act("banner.dismiss", "Dismiss", kind="text"),
            )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def dismiss(self):
        self.hidden = True
        return update_with(self)

    @action(caps=())
    def show(self):
        self.hidden = False
        return update_with(self)


def demo() -> None:
    app = App.boot("Overlays", strict_caps=False)
    app.add(Toasts, Confirm, Lightbox, Palette, Banner)
    print("toast", app.dispatch("toasts.push", message="hi"))
    print("ask", app.dispatch("confirm.ask", id="oak-02"))
    print("light", app.dispatch("lightbox.open_box"))
    strict = App.boot("Overlays", strict_caps=True)
    strict.add(Confirm)
    try:
        strict.dispatch("confirm.confirm")
        print("UNEXPECTED confirm")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
