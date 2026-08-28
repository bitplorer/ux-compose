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


class Chips(Component):
    """Named tags. The set is RefState. Stamp dirties the unit.

    Same encoding as a multi-select. ``SUGGESTIONS`` is ``(key, label)``.
    """

    id = "chips"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-5 "
        "overflow-x-hidden rounded-[1.75rem] border border-stone-200/90 bg-white p-6 text-stone-900 "
        "shadow-[0_1px_0_rgba(22,21,19,0.04),0_24px_48px_-28px_rgba(22,21,19,0.4)] "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-xs font-medium uppercase tracking-[0.2em] text-stone-500 "
        "dark:text-stone-400"
    )
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_row = "flex min-w-0 flex-wrap gap-2"
    class_chip = (
        "inline-flex min-h-11 items-center gap-1 rounded-full border border-stone-200 "
        "bg-stone-50 pl-4 pr-1 text-sm font-medium text-stone-800 "
        "dark:border-stone-700 dark:bg-stone-900 dark:text-stone-100"
    )
    class_x = (
        "inline-flex size-9 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent text-stone-400 hover:bg-stone-200 hover:text-stone-900 "
        "active:scale-95 focus-visible:outline-none focus-visible:ring-2 "
        "focus-visible:ring-stone-900/15 dark:hover:bg-stone-800 dark:hover:text-stone-50"
    )
    class_suggest = (
        "min-h-11 cursor-pointer rounded-full border border-dashed border-stone-300 "
        "bg-transparent px-4 text-sm font-medium text-stone-500 "
        "hover:border-stone-400 hover:text-stone-900 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:border-stone-600 dark:text-stone-400 dark:hover:text-stone-50"
    )
    class_empty = "m-0 text-sm text-stone-500 dark:text-stone-400"
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

    def render(self):
        have = tuple(self.tags or ())
        have_set = set(have)
        chips = []
        for tag in have:
            chips.append(
                span(
                    self._label(tag),
                    button(
                        span(f"Remove {self._label(tag)}", className=self.class_sr),
                        "×",
                        type="button",
                        className=self.class_x,
                        **bind(self.remove, tag=tag),
                    ),
                    id=f"{self.id}-chip-{tag}",
                    className=self.class_chip,
                )
            )
        suggestions = [
            button(
                f"+ {lab}",
                type="button",
                id=f"{self.id}-add-{key}",
                className=self.class_suggest,
                **bind(self.add, tag=key),
            )
            for key, lab in self._suggestions()
            if key not in have_set
        ]
        return div(
            span("Tags", className=self.class_kicker),
            h2("What it is made of", className=self.class_title),
            p("Names in a set. Stamp dirties. Domain tags stay Host-owned.", className=self.class_lede),
            div(*chips, className=self.class_row) if chips else p("No tags yet.", className=self.class_empty),
            div(*suggestions, className=self.class_row) if suggestions else span("", className=self.class_sr),
            id=self.id,
            className=self.class_card,
            data_count=str(len(have)),
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
