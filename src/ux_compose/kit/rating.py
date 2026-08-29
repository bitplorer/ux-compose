"""Drop-in star rating — named, never numeric MorphState.

Host seam: override ``STARS`` and ``on_rate(key)``. Picking is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
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
    path,
    span,
    svg,
)


def _star(filled: bool):
    return svg(
        path(
            d="M12 3.1 14.7 8.8l6.3.7-4.7 4.3 1.3 6.2L12 16.9 6.4 20l1.3-6.2L3 9.5l6.3-.7z",
            fill="currentColor" if filled else "none",
            stroke="currentColor",
            **{
                "stroke-width": "1.45",
                "stroke-linejoin": "round",
                "stroke-linecap": "round",
            },
        ),
        **{
            "viewBox": "0 0 24 24",
            "aria-hidden": "true",
            "focusable": "false",
        },
        className="pointer-events-none block h-6 w-6 drop-shadow-sm",
    )


def _rate_plan(cid: str = "rating"):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene("rating-set").enter(f"#{cid}-face", rise.enter(ms=140))
    except Exception:
        return None


class Rating(Component):
    """Five named stars. The value is MorphState, never MorphState(int).

    ``STARS`` is ``(key, label)``. Override on the copy.
    """

    id = "rating"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-6 "
        "rounded-[1.85rem] border border-stone-900/[0.07] bg-[#fdfcf8] p-7 text-stone-900 "
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
    class_lede = "m-0 max-w-[34ch] text-[0.9375rem] leading-relaxed text-stone-500 dark:text-stone-400"
    class_face = (
        "relative overflow-hidden rounded-[1.35rem] bg-gradient-to-br "
        "from-amber-50 via-[#fdfcf8] to-stone-100 px-6 py-7 "
        "ring-1 ring-amber-900/10 "
        "dark:from-amber-950/40 dark:via-[#141311] dark:to-stone-900 dark:ring-amber-500/15"
    )
    class_ghost = (
        "pointer-events-none absolute -right-1 -top-3 font-serif text-[7.5rem] font-medium "
        "leading-none tracking-tight text-amber-900/[0.08] dark:text-amber-100/[0.08]"
    )
    class_word = (
        "relative m-0 font-serif text-5xl font-semibold leading-none tracking-[-0.04em] "
        "text-stone-900 dark:text-stone-50"
    )
    class_caption = (
        "relative m-0 mt-2 text-[0.8125rem] text-stone-500 dark:text-stone-400"
    )
    class_row = (
        "relative mt-6 inline-flex items-center gap-0.5 rounded-full bg-white/80 p-1 "
        "shadow-[inset_0_0_0_1px_rgba(22,21,19,0.06)] "
        "dark:bg-stone-900/70 dark:shadow-[inset_0_0_0_1px_rgba(255,255,255,0.08)]"
    )
    class_star = (
        "inline-flex size-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent p-0 text-stone-300 transition duration-200 "
        "hover:text-amber-400 hover:scale-110 active:scale-95 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-700/35 "
        "motion-reduce:transition-none motion-reduce:hover:scale-100 "
        "dark:text-stone-600 dark:hover:text-amber-300"
    )
    class_star_on = (
        "inline-flex size-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent p-0 text-amber-700 transition duration-200 "
        "hover:text-amber-600 hover:scale-110 active:scale-95 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-700/35 "
        "motion-reduce:transition-none motion-reduce:hover:scale-100 "
        "dark:text-amber-400 dark:hover:text-amber-300"
    )
    class_sr = "sr-only"

    STARS = (
        ("one", "One"),
        ("two", "Two"),
        ("three", "Three"),
        ("four", "Four"),
        ("five", "Five"),
    )

    stars = MorphState("three")

    def on_rate(self, key: str) -> str:
        """Host seam. Return toast copy."""
        return key

    def _stars(self):
        return tuple(self.STARS)

    def _current(self):
        rows = self._stars()
        keys = [row[0] for row in rows]
        cur = str(self.stars or keys[0])
        if cur not in keys:
            cur = keys[2] if len(keys) > 2 else keys[0]
        return keys.index(cur), cur, rows

    def render(self):
        idx, cur, rows = self._current()
        label = rows[idx][1]
        buttons = []
        for i, (key, lab) in enumerate(rows):
            on = i <= idx
            buttons.append(
                button(
                    span(lab, className=self.class_sr),
                    _star(on),
                    type="button",
                    id=f"{self.id}-star-{key}",
                    className=self.class_star_on if on else self.class_star,
                    role="radio",
                    aria_checked="true" if key == cur else "false",
                    aria_label=f"{lab} of {len(rows)}",
                    **bind(self.set, value=key),
                )
            )
        return div(
            span("Held", className=self.class_kicker),
            h2("How does it sit?", className=self.class_title),
            p("Names survive the session plane. Ints do not.", className=self.class_lede),
            div(
                span(str(idx + 1), className=self.class_ghost, aria_hidden="true"),
                p(label, className=self.class_word),
                p(f"{label} · of {len(rows)}", className=self.class_caption),
                div(
                    *buttons,
                    className=self.class_row,
                    role="radiogroup",
                    aria_label="Piece rating",
                ),
                id=f"{self.id}-face",
                className=self.class_face,
            ),
            id=self.id,
            className=self.class_card,
            data_stars=cur,
        )

    @action(caps=())
    def set(self, value: str = "three"):
        keys = {row[0] for row in self._stars()}
        self.stars = value if value in keys else self._stars()[0][0]
        return update_with(
            self,
            _rate_plan(self.id),
            extra_ops=[notify(self.on_rate(str(self.stars)))],
        )
