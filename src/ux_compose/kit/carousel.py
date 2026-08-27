"""Drop-in carousel — named slides, never a quantity MorphState.

Host seam: override ``SLIDES``. Prev / next compute the neighbor key.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

Live: the root ``id`` is the region. Channel picks it up.
Host ``swipe.horizontal``. Prev accepts ``click swipe.right``,
Next accepts ``click swipe.left`` — same synthesizer as PullRefresh,
no extra JS and no second attribute family.

Chrome: Prev / Next sit on the stage (left / right), not in a wrapping
rail. Dots are the only bottom row. The index is a watermark.
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


def _chevron(direction: str):
    """24px stroke chevron. ``direction`` is ``left`` or ``right``."""
    d = "M15 6 9 12l6 6" if direction == "left" else "M9 6l6 6-6 6"
    return svg(
        path(
            d=d,
            fill="none",
            stroke="currentColor",
            **{
                "stroke-width": "1.75",
                "stroke-linecap": "round",
                "stroke-linejoin": "round",
            },
        ),
        **{
            "viewBox": "0 0 24 24",
            "aria-hidden": "true",
            "focusable": "false",
        },
        className="pointer-events-none block h-5 w-5",
    )


class Carousel(Component):
    """One named slide at a time.

    ``SLIDES`` is ``(key, kicker, title, body)``. Override on the copy.

    Swipe on the stage is a synthesizer: finger or pointer, same Intent
    path as Prev / Next. Dots are named jumps. The pip never changes
    the slot width, so the cursor does not jump under a click.
    """

    id = "carousel"

    class_card = (
        "[grid-area:card] relative mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 self-start "
        "overflow-hidden rounded-3xl border border-stone-200 bg-white p-5 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 max-w-sm text-sm leading-relaxed text-stone-500"
    class_stage = (
        "relative flex min-h-56 touch-pan-y select-none flex-col justify-end "
        "rounded-2xl bg-stone-50 px-16 py-8"
    )
    class_copy = "relative z-[1] flex flex-col gap-3"
    class_index = (
        "pointer-events-none absolute right-5 top-4 z-0 font-serif text-6xl font-medium "
        "leading-none tracking-tight text-stone-200"
    )
    class_nav = (
        "absolute top-1/2 z-10 inline-flex size-11 -translate-y-1/2 cursor-pointer items-center "
        "justify-center rounded-full border-0 bg-white/90 text-stone-900 shadow-sm "
        "backdrop-blur-sm hover:bg-white hover:shadow "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/20"
    )
    class_nav_prev = "left-3"
    class_nav_next = "right-3"
    class_dots = "flex flex-nowrap items-center justify-center"
    class_dot = (
        "inline-flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent p-0 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_pip = "pointer-events-none block h-2 w-2 rounded-full bg-stone-300"
    class_pip_on = "pointer-events-none block h-2 w-6 rounded-full bg-stone-800"
    class_sr = "sr-only"

    SLIDES = (
        ("linen", "Cloth", "Linen work shirt", "Cut to the shoulder. One region morphs."),
        ("oak", "Wood", "Oak serving board", "Wax, then rest. The key is a name."),
        ("wool", "Cloth", "Wool throw", "Winter weight. Caps stay off chrome."),
        ("clay", "Earth", "Clay pourer", "Brush, never soak. Neighbor keys, not +1."),
    )

    slide = MorphState("linen")

    def _slides(self):
        return tuple(self.SLIDES)

    def _current(self):
        rows = self._slides()
        keys = [row[0] for row in rows]
        cur = str(self.slide or keys[0])
        if cur not in keys:
            cur = keys[0]
        return keys.index(cur), cur, rows, keys

    def _nav(self, direction: str, fn, label: str):
        side = self.class_nav_prev if direction == "left" else self.class_nav_next
        signal = "click swipe.right" if direction == "left" else "click swipe.left"
        slot = "prev" if direction == "left" else "next"
        return button(
            span(label, className=self.class_sr),
            _chevron(direction),
            type="button",
            id=f"{self.id}-{slot}",
            className=f"{self.class_nav} {side}",
            aria_label=label,
            data_channel_on=signal,
            **bind(fn),
        )

    def render(self):
        idx, cur, rows, keys = self._current()
        _key, kicker, title, body = rows[idx]
        n = len(keys)
        dots = [
            button(
                span(ttl, className=self.class_sr),
                span("", className=self.class_pip_on if k == cur else self.class_pip),
                type="button",
                id=f"{self.id}-dot-{k}",
                className=self.class_dot,
                aria_label=ttl,
                **({"aria_current": "true"} if k == cur else {}),
                **bind(self.goto, key=k),
            )
            for k, _lab, ttl, _b in rows
        ]
        return div(
            div(
                span(
                    f"{idx + 1:02d}",
                    className=self.class_index,
                    aria_hidden="true",
                ),
                div(
                    span(kicker, className=self.class_kicker),
                    h2(title, className=self.class_title, id=f"{self.id}-title"),
                    p(body, className=self.class_lede),
                    className=self.class_copy,
                    aria_live="polite",
                ),
                self._nav("left", self.prev, "Previous slide"),
                self._nav("right", self.next, "Next slide"),
                className=self.class_stage,
            ),
            div(*dots, className=self.class_dots, role="group", aria_label="Slides"),
            id=self.id,
            className=self.class_card,
            role="region",
            aria_roledescription="carousel",
            aria_labelledby=f"{self.id}-title",
            data_slide=cur,
            data_of=str(n),
            data_channel_id=self.id,
            data_channel_on="swipe.horizontal threshold:48",
        )

    @action(caps=())
    def goto(self, key: str = ""):
        keys = {row[0] for row in self._slides()}
        self.slide = key if key in keys else self._slides()[0][0]
        return update_with(self, extra_ops=[notify(str(self.slide))])

    @action(caps=())
    def next(self):
        idx, _cur, _rows, keys = self._current()
        self.slide = keys[(idx + 1) % len(keys)]
        return update_with(self)

    @action(caps=())
    def prev(self):
        idx, _cur, _rows, keys = self._current()
        self.slide = keys[(idx - 1) % len(keys)]
        return update_with(self)
