"""Drop-in CTA — titled call with a public (or Cap) action.

Host seam: construct kwargs OR subclass.
Accepted: ``title``, ``body``, ``action`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``done``. Caps: none by default. A11y: region labelledby title.
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
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


class Cta(Kit):
    """One ask. The button is the verb."""

    id = "cta"
    _SEAMS = {'title': 'TITLE', 'body': 'BODY', 'action': 'ACTION'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col "
        "items-start gap-3 rounded-3xl border border-stone-200 bg-white p-8 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn = (
        "mt-1 inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )

    TITLE = "Join the winter list"
    BODY = "A letter when the linen lands. No spam, ever."
    ACTION = "Join"

    done = MorphState(False)

    def on_act(self) -> str:
        return "Joined"

    def render(self):
        title_id = f"{self.id}-title"
        done = bool(self.done)
        return self.kit_shell(
            h2(self.TITLE, id=title_id, className=self.class_title),
            p("You're on the list." if done else self.BODY, className=self.class_lede),
            button(
                "Joined" if done else self.ACTION,
                type="button",
                className=self.class_btn,
                disabled=True if done else None,
                **bind(self.act),
            ) if not done else span("Joined", className="text-sm font-medium text-emerald-700"),
            id=self.id,
            className=self.class_card,
            chrome=(span("Invite", className=self.class_kicker),),
            role="region",
            aria_labelledby=title_id,
            data_done="1" if done else "0",
        )

    @action(caps=())
    def act(self):
        self.done = True
        return update_with(self, extra_ops=[notify(self.on_act())])
