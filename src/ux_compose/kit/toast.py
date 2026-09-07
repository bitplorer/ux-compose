"""Drop-in toast host — server list is authority.

Items live in RefState. ``dirty`` is the qualitative MorphState so the
unit morphs. Push is public. The stack is a fixed corner — the card is
the demo controls.

Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    HAS_DOM,
    Component,
    MorphState,
    RefState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    li,
    p,
    span,
    ul,
)
from ux_compose.helpers import html_attrs, html_escape


class Toast(Component):
    """Stack of one-shot messages. The server list is the truth.

    ``push(message=)`` appends. ``dismiss(id=)`` removes one. ``clear`` empties.
    """

    id = "toast"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_row = "flex flex-wrap items-center gap-2.5"
    class_stack = (
        "fixed bottom-6 right-6 z-50 m-0 flex w-[min(22rem,calc(100vw-2rem))] "
        "list-none flex-col gap-2 p-0"
    )
    class_item = (
        "flex items-center justify-between gap-3 rounded-2xl border "
        "border-emerald-100 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 shadow-sm"
    )
    class_x = (
        "min-h-11 min-w-11 cursor-pointer rounded-full border-0 bg-transparent "
        "text-sm font-medium text-inherit hover:bg-emerald-100"
    )

    items = RefState(())
    dirty = MorphState("idle")
    _seq = RefState(0)

    def _mark_dirty(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        if HAS_DOM and div is not None:
            return self._render_tree()
        return self._render_html()

    def _render_tree(self):
        rows = list(self.items or ())[-4:]
        n = len(rows)
        lis = [
            li(
                span(str(row.get("message", ""))),
                button(
                    "Dismiss",
                    type="button",
                    className=self.class_x,
                    **bind(self.dismiss, id=str(row.get("id", ""))),
                ),
                id=f"toast-{row.get('id')}",
                className=self.class_item,
                role="status",
            )
            for row in rows
        ]
        stack = ul(*lis, className=self.class_stack) if lis else span("", className="sr-only")
        status = (
            p(f"{n} notice" + ("" if n == 1 else "s") + " on the stack.", className=self.class_lede)
            if n
            else p("No notices yet.", className=self.class_lede)
        )
        return div(
            span("Notices", className=self.class_kicker),
            h2("Saved to the table", className=self.class_title),
            p("notify() is the Op. This unit shows them.", className=self.class_lede),
            status,
            div(
                button(
                    "Push note",
                    type="button",
                    className=self.class_btn_primary,
                    **bind(self.push, message="Saved to the table"),
                ),
                button(
                    "Clear",
                    type="button",
                    className=self.class_btn_ghost,
                    **bind(self.clear),
                ),
                className=self.class_row,
            ),
            stack,
            id=self.id,
            className=self.class_card,
        )

    def _render_html(self):
        """L1 / Py3.13 fragment. Morph target is ``#toast`` — not a document."""
        rows = list(self.items or ())[-4:]
        n = len(rows)
        lis = []
        for row in rows:
            dismiss = html_attrs(bind(self.dismiss, id=str(row.get("id", ""))))
            msg = html_escape(row.get("message", ""))
            rid = html_escape(row.get("id", ""))
            lis.append(
                f'<li id="toast-{rid}" class="{self.class_item}" role="status">'
                f"<span>{msg}</span>"
                f'<button type="button" class="{self.class_x}" {dismiss}>Dismiss</button>'
                f"</li>"
            )
        stack = (
            f'<ul class="{self.class_stack}">{"".join(lis)}</ul>'
            if lis
            else '<span class="sr-only"></span>'
        )
        if n:
            noun = "notice" if n == 1 else "notices"
            status = f'<p class="{self.class_lede}">{n} {noun} on the stack.</p>'
        else:
            status = f'<p class="{self.class_lede}">No notices yet.</p>'
        push = html_attrs(bind(self.push, message="Saved to the table"))
        clear = html_attrs(bind(self.clear))
        return (
            f'<div id="{html_escape(self.id)}" class="{self.class_card}">'
            f'<span class="{self.class_kicker}">Notices</span>'
            f'<h2 class="{self.class_title}">Saved to the table</h2>'
            f'<p class="{self.class_lede}">notify() is the Op. This unit shows them.</p>'
            f"{status}"
            f'<div class="{self.class_row}">'
            f'<button type="button" class="{self.class_btn_primary}" {push}>Push note</button>'
            f'<button type="button" class="{self.class_btn_ghost}" {clear}>Clear</button>'
            f"</div>"
            f"{stack}"
            f"</div>"
        )

    @action(caps=())
    def push(self, message: str = "Saved"):
        self._seq = int(self._seq or 0) + 1
        row = {"id": str(self._seq), "message": message or "Saved"}
        self.items = tuple(self.items or ()) + (row,)
        self._mark_dirty()
        return update_with(self, extra_ops=[notify(row["message"])])

    @action(caps=())
    def dismiss(self, id: str = ""):
        self.items = tuple(
            row for row in (self.items or ()) if str(row.get("id")) != str(id)
        )
        self._mark_dirty()
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.items = ()
        self._mark_dirty()
        return update_with(self)
