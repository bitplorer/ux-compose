"""Drop-in chips — tag set as RefState.

Host seam: override ``SUGGESTIONS`` and ``on_add`` / ``on_remove``.
Add / remove are public. Domain tags stay Host-owned.
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
    p,
    span,
)


_CHIP_ON = {
    "linen": "bg-[#e8dcc8] text-[#3d2914] ring-1 ring-[#c9b89a]",
    "oak": "bg-[#c4a574] text-[#3d2914] ring-1 ring-[#8b6914]/40",
    "wool": "bg-[#d4c4b0] text-[#3d2914] ring-1 ring-[#9a8470]/40",
    "clay": "bg-[#c9a882] text-[#3d2914] ring-1 ring-[#a67c52]/40",
    "quiet": "bg-stone-800 text-stone-50 ring-1 ring-stone-900",
    "winter": "bg-sky-100 text-sky-950 ring-1 ring-sky-200",
}

_DOT = {
    "linen": "bg-[#c9b89a]",
    "oak": "bg-[#8b6914]",
    "wool": "bg-[#9a8470]",
    "clay": "bg-[#a67c52]",
    "quiet": "bg-stone-400",
    "winter": "bg-sky-400",
}


class Chips(Component):
    """Named tags. The set is RefState. Stamp dirties the unit.

    Same encoding as a multi-select. ``SUGGESTIONS`` is ``(key, label)``.
    """

    id = "chips"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-6 "
        "overflow-x-hidden rounded-[1.85rem] border border-stone-900/[0.07] bg-[#fdfcf8] p-7 text-stone-900 "
        "shadow-[0_0_0_1px_rgba(22,21,19,0.03),0_1px_2px_rgba(22,21,19,0.04),0_28px_56px_-24px_rgba(22,21,19,0.2)] "
        "dark:border-white/10 dark:bg-[#141311] dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-[0.6875rem] font-medium uppercase tracking-[0.22em] text-stone-400 "
        "dark:text-stone-500"
    )
    class_title = (
        "m-0 font-serif text-[1.85rem] font-semibold leading-[1.12] tracking-[-0.03em]"
    )
    class_lede = (
        "m-0 max-w-[36ch] text-[0.9375rem] leading-relaxed text-stone-500 "
        "dark:text-stone-400"
    )
    class_row = "flex min-w-0 flex-wrap gap-2"
    class_chip = (
        "inline-flex min-h-11 items-center gap-2 rounded-full pl-3.5 pr-1 "
        "text-[0.82rem] font-medium"
    )
    class_dot = "h-1.5 w-1.5 rounded-full"
    class_x = (
        "inline-flex size-9 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent text-current/60 hover:bg-black/10 hover:text-current "
        "active:scale-95 focus-visible:outline-none focus-visible:ring-2 "
        "focus-visible:ring-stone-900/15"
    )
    class_suggest = (
        "inline-flex min-h-11 items-center gap-1.5 rounded-full border border-dashed "
        "border-stone-900/15 bg-transparent px-3.5 text-[0.82rem] font-medium "
        "text-stone-500 transition hover:border-stone-900/30 hover:text-stone-800 "
        "active:scale-[0.98] focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:border-white/15 dark:text-stone-400 dark:hover:text-stone-50"
    )
    class_empty = "m-0 text-[0.8rem] text-stone-400"
    class_held = "m-0 text-[0.8rem] leading-relaxed text-stone-400"
    class_sr = "sr-only"

    SUGGESTIONS = (
        ("linen", "Linen"),
        ("oak", "Oak"),
        ("wool", "Wool"),
        ("quiet", "Quiet"),
        ("winter", "Winter"),
    )

    tags = RefState(("linen", "quiet"))
    stamp = MorphState("idle")

    def on_add(self, tag: str) -> str:
        return tag

    def on_remove(self, tag: str) -> str:
        return tag

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def _suggestions(self):
        return tuple(self.SUGGESTIONS)

    def _label(self, key: str) -> str:
        for k, lab in self._suggestions():
            if k == key:
                return lab
        return key

    def _chip_on(self, key: str) -> str:
        return _CHIP_ON.get(key, "bg-stone-200 text-stone-800 ring-1 ring-stone-300")

    def render(self):
        have = tuple(self.tags or ())
        have_set = set(have)
        chips = []
        for tag in have:
            chips.append(
                span(
                    span(
                        "",
                        className=f"{self.class_dot} {_DOT.get(tag, 'bg-stone-400')}",
                        aria_hidden="true",
                    ),
                    self._label(tag),
                    button(
                        span(f"Remove {self._label(tag)}", className=self.class_sr),
                        "×",
                        type="button",
                        className=self.class_x,
                        **bind(self.remove, tag=tag),
                    ),
                    id=f"{self.id}-chip-{tag}",
                    className=f"{self.class_chip} {self._chip_on(tag)}",
                )
            )
        suggestions = [
            button(
                span(
                    "",
                    className=f"{self.class_dot} {_DOT.get(key, 'bg-stone-300')}",
                    aria_hidden="true",
                ),
                lab,
                type="button",
                id=f"{self.id}-add-{key}",
                className=self.class_suggest,
                **bind(self.add, tag=key),
            )
            for key, lab in self._suggestions()
            if key not in have_set
        ]
        n = len(have)
        held = (
            "Nothing chosen."
            if n == 0
            else f"{n} held · {', '.join(self._label(t) for t in have)}"
        )
        return div(
            span("Tags", className=self.class_kicker),
            h2("What it is made of", className=self.class_title),
            p(
                "Names in a set. Stamp dirties. Domain tags stay Host-owned.",
                className=self.class_lede,
            ),
            div(*chips, className=self.class_row)
            if chips
            else p("No tags yet.", className=self.class_empty),
            div(*suggestions, className=self.class_row)
            if suggestions
            else span("", className=self.class_sr),
            p(held, className=self.class_held),
            id=self.id,
            className=self.class_card,
            data_count=str(n),
        )

    @action(caps=())
    def add(self, tag: str = ""):
        keys = {row[0] for row in self._suggestions()}
        if not tag or tag not in keys or tag in tuple(self.tags or ()):
            return update_with(self)
        self.tags = tuple(self.tags or ()) + (tag,)
        self._tick()
        return update_with(self, extra_ops=[notify(self.on_add(tag))])

    @action(caps=())
    def remove(self, tag: str = ""):
        self.tags = tuple(t for t in (self.tags or ()) if t != tag)
        self._tick()
        return update_with(self, extra_ops=[notify(self.on_remove(tag))])
