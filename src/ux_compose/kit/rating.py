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
                "stroke-width": "1.6",
                "stroke-linejoin": "round",
                "stroke-linecap": "round",
            },
        ),
        **{
            "viewBox": "0 0 24 24",
            "aria-hidden": "true",
            "focusable": "false",
        },
        className="pointer-events-none block h-7 w-7",
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
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-5 "
        "rounded-[1.75rem] border border-stone-200/90 bg-white p-6 text-stone-900 "
        "shadow-[0_1px_0_rgba(22,21,19,0.04),0_24px_48px_-28px_rgba(22,21,19,0.4)] "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-xs font-medium uppercase tracking-[0.2em] text-stone-500 "
        "dark:text-stone-400"
    )
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_face = (
        "flex flex-col gap-3 rounded-2xl bg-stone-900 px-5 py-6 text-stone-50 "
        "dark:bg-stone-100 dark:text-stone-900"
    )
    class_mark = (
        "font-serif text-6xl font-medium leading-none tracking-tight text-amber-200 "
        "dark:text-amber-800"
    )
    class_caption = "m-0 text-sm text-stone-300 dark:text-stone-600"
    class_row = "flex items-center gap-1"
    class_star = (
        "inline-flex size-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent p-0 text-stone-300 transition "
        "hover:text-amber-200 hover:scale-105 active:scale-95 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/50 "
        "dark:text-stone-400 dark:hover:text-amber-700 dark:focus-visible:ring-amber-800/40"
    )
    class_star_on = (
        "inline-flex size-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent p-0 text-amber-300 transition "
        "hover:text-amber-200 hover:scale-105 active:scale-95 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-200/50 "
        "dark:text-amber-700 dark:hover:text-amber-600"
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
                span(str(idx + 1), className=self.class_mark, aria_hidden="true"),
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
