"""Drop-in hero — titled landing band with a public CTA.

Host seam: override ``TITLE`` / ``BODY`` / ``on_act()``. Acting is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``done``. Caps: none. A11y: region labelledby title.
"""

from __future__ import annotations

from ux_compose import (
    Component,
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


class Hero(Component):
    """First impression. The CTA is chrome, not a Cap."""

    id = "hero"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] flex-col "
        "gap-4 rounded-3xl border border-stone-200 bg-stone-900 px-8 py-12 text-stone-50 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 max-w-lg font-serif text-4xl font-semibold tracking-tight"
    class_lede = "m-0 max-w-md text-sm leading-relaxed text-stone-300"
    class_btn = (
        "mt-2 inline-flex min-h-11 w-fit cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-50 px-5 text-sm font-medium text-stone-900 hover:bg-white"
    )

    TITLE = "Made to be kept"
    BODY = "Cloth, wood, and earth — one catalog, morphing in place."
    ACTION = "Open the catalog"

    done = MorphState(False)

    def on_act(self) -> str:
        return "Opened"

    def render(self):
        title_id = f"{self.id}-title"
        done = bool(self.done)
        return div(
            span("Studio", className=self.class_kicker),
            h2(self.TITLE, id=title_id, className=self.class_title),
            p(self.BODY, className=self.class_lede),
            button(
                "You're in" if done else self.ACTION,
                type="button",
                className=self.class_btn,
                **bind(self.act),
            ),
            id=self.id,
            className=self.class_card,
            role="region",
            aria_labelledby=title_id,
            data_done="1" if done else "0",
        )

    @action(caps=())
    def act(self):
        self.done = True
        return update_with(self, extra_ops=[notify(self.on_act())])
