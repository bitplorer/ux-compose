"""Drop-in toast host — server list is authority.

Items live in RefState. ``stamp`` is the qualitative dirty tick so the
unit morphs. Push is public. The stack is a fixed corner — the card is
the demo controls.

Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
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
    stamp = MorphState("idle")
    _seq = RefState(0)

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def render(self):
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

    @action(caps=())
    def push(self, message: str = "Saved"):
        self._seq = int(self._seq or 0) + 1
        row = {"id": str(self._seq), "message": message or "Saved"}
        self.items = tuple(self.items or ()) + (row,)
        self._tick()
        return update_with(self, extra_ops=[notify(row["message"])])

    @action(caps=())
    def dismiss(self, id: str = ""):
        self.items = tuple(
            row for row in (self.items or ()) if str(row.get("id")) != str(id)
        )
        self._tick()
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.items = ()
        self._tick()
        return update_with(self)
