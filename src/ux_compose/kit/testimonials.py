"""Drop-in testimonials — named quotes, MorphState index key.

Host seam: construct kwargs OR subclass.
Accepted: ``quotes`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``which``. Caps: none. A11y: ``figure`` labelledby; prev/next
named. Quote is a name, not a quantity.
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


class Testimonials(Kit):
    """One named quote at a time. ``which`` is a key from QUOTES."""

    id = "testimonials"
    _SEAMS = {'quotes': 'QUOTES'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_quote = "m-0 font-serif text-xl font-medium tracking-tight"
    class_row = "flex gap-2"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium"
    )

    QUOTES = (
        ("ada", "It stays on the table.", "Ada"),
        ("oak", "Waxed, then rested.", "Oak workshop"),
        ("lin", "Cut to the shoulder.", "Linen mill"),
    )

    which = MorphState("ada")

    def _current(self):
        items = tuple(self.QUOTES)
        cur = str(self.which or items[0][0])
        for row in items:
            if row[0] == cur:
                return row
        return items[0]

    def render(self):
        key, quote, who = self._current()
        qid = f"{self.id}-q"
        return self.kit_shell(
            p(quote, id=qid, className=self.class_quote),
            p(f"— {who}", className=self.class_lede),
            div(
                button("Previous", type="button", className=self.class_btn, **bind(self.prev)),
                button("Next", type="button", className=self.class_btn, **bind(self.next)),
                className=self.class_row,
            ),
            id=self.id,
            className=self.class_card,
            role="region",
            aria_labelledby=qid,
            data_which=key,
            chrome=(
                span("Voices", className=self.class_kicker),
                h2("What they keep", className=self.class_title),
            ),
        )

    def _shift(self, delta: int):
        keys = [row[0] for row in self.QUOTES]
        i = keys.index(str(self.which)) if str(self.which) in keys else 0
        self.which = keys[(i + delta) % len(keys)]

    @action(caps=())
    def next(self):
        self._shift(1)
        return update_with(self, extra_ops=[notify(str(self.which))])

    @action(caps=())
    def prev(self):
        self._shift(-1)
        return update_with(self, extra_ops=[notify(str(self.which))])
