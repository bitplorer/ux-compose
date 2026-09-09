"""Drop-in empty state — titled void with a public call to action.

Host seam: render slots OR subclass.
Accepted: ``title``, ``body``, ``action`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``filled``. Caps: none. A11y: region labelledby title; status
when empty.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    MorphState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    p,
    span,
)


class EmptyState(Component):
    """Nothing on the table. The CTA seeds the first row."""

    id = "emptystate"
    _SEAMS = {'title': 'TITLE', 'body': 'BODY', 'action': 'ACTION'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col "
        "items-center gap-3 rounded-3xl border border-dashed border-stone-300 bg-white "
        "px-6 py-10 text-center text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 max-w-sm text-sm leading-relaxed text-stone-500"
    class_btn = (
        "mt-2 inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )

    TITLE = "Nothing on the table"
    BODY = "Pin a piece from the catalog. Opening this region is public."
    ACTION = "Add a piece"

    filled = MorphState(False)

    def on_act(self) -> str:
        return "Added"

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        filled = bool(self.filled)
        title_id = f"{self.id}-title"
        if filled:
            return kit_shell(self,
                span("Ready", className=self.class_kicker),
                h2("A piece is here", id=title_id, className=self.class_title),
                p("The empty state morphs away. Clear to see it again.", className=self.class_lede),
                button("Clear", type="button", className=self.class_btn, **bind(self.clear)),
                id=self.id,
                className=self.class_card.replace("border-dashed border-stone-300", "border-stone-200"),
                aria_labelledby=title_id,
                data_filled="1",
            )
        return kit_shell(self,
            h2(self.TITLE, id=title_id, className=self.class_title),
            p(self.BODY, className=self.class_lede, role="status"),
            button(self.ACTION, type="button", className=self.class_btn, **bind(self.act)),
            chrome=(span("Empty", className=self.class_kicker),),
            id=self.id,
            className=self.class_card,
            aria_labelledby=title_id,
            data_filled="0",
        )

    @action(caps=())
    def act(self):
        self.filled = True
        return update_with(self, extra_ops=[notify(self.on_act())])

    @action(caps=())
    def clear(self):
        self.filled = False
        return update_with(self)
