"""Drop-in card — titled region with an optional action.

Host seam: construct kwargs OR subclass.
Accepted: ``title``, ``body``, ``action`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts. Act is public chrome unless you add a Cap in the copy.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``pressed``. Caps: none by default. A11y: article labelledby title.
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
    MorphState,
    action,
    bind,
    notify,
    update_with,
    article,
    button,
    h2,
    p,
    span,
)


class Card(Kit):
    """One titled piece. The action is a named public verb on this unit."""

    id = "card"
    _SEAMS = {'title': 'TITLE', 'body': 'BODY', 'action': 'ACTION'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )

    TITLE = "Oak serving board"
    BODY = "Waxed, then rested. One region morphs. The page does not remount."
    ACTION = "Pin to the desk"

    pressed = MorphState(False)

    def on_act(self) -> str:
        return "Pinned"

    def render(self):
        title_id = f"{self.id}-title"
        on = bool(self.pressed)
        kids = []
        if getattr(self, "shell", True):
            kids.append(span("Piece", className=self.class_kicker))
        kids.extend(
            [
                h2(self.TITLE, id=title_id, className=self.class_title),
                p(self.BODY, className=self.class_lede),
                button(
                    "Pinned" if on else self.ACTION,
                    type="button",
                    className=self.class_btn,
                    aria_pressed="true" if on else "false",
                    **bind(self.act),
                ),
            ]
        )
        return article(
            *kids,
            id=self.id,
            className=self.class_card if getattr(self, "shell", True) else "",
            aria_labelledby=title_id,
            data_pressed="1" if on else "0",
        )

    @action(caps=())
    def act(self):
        self.pressed = not bool(self.pressed)
        return update_with(self, extra_ops=[notify(self.on_act())])
