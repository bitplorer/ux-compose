"""Drop-in avatar — initials stand-in, labelled image role.

Host seam: override ``name``. Caps: none.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: none. RefState: ``name``. A11y: ``role=img`` ``aria-label``.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    RefState,
    action,
    bind,
    update_with,
    button,
    div,
    h2,
    p,
    span,
)


class Avatar(Component):
    """Face without a file. The accessible name is the person."""

    id = "avatar"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_mark = (
        "flex h-16 w-16 items-center justify-center rounded-full bg-stone-800 "
        "text-lg font-semibold text-stone-50"
    )
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium"
    )

    name = RefState("Ada Lovelace")

    def render(self):
        who = str(self.name or "You")
        bits = [p for p in who.split() if p]
        initials = "".join(b[0] for b in bits[:2]).upper() or "Y"
        return div(
            span("You", className=self.class_kicker),
            h2("Portrait", className=self.class_title),
            p(who, className=self.class_lede),
            span(initials, className=self.class_mark, role="img", aria_label=who),
            button("Rename", type="button", className=self.class_btn, **bind(self.rename)),
            id=self.id,
            className=self.class_card,
        )

    @action(caps=())
    def rename(self):
        self.name = "Ada Lovelace" if "Ada" not in str(self.name or "") else "Oak Atelier"
        return update_with(self)
