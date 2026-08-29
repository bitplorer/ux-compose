"""Drop-in lightbox — named slides, overlay presence.

Host seam: override ``SLIDES``. Opening is public. Index is a name, not an int.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

The resting card stays in flow; the overlay is presence on top of it.
The card is not a containing block (no ``relative``, no overflow clip)
so ``fixed`` overlay is not trapped. Panel and scrim keep stable ids.
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


def _open_plan(cid: str = "lightbox"):
    try:
        from ux_compose import scene, fade, rise

        if scene is None or fade is None or rise is None:
            return None
        return (
            scene("lightbox-open")
            .enter(f"#{cid}-scrim", fade.enter(ms=120))
            .enter(f"#{cid}-panel", rise.enter(ms=180))
        )
    except Exception:
        return None


_WASH = {
    "linen": "bg-gradient-to-br from-[#e8dcc8] via-[#c9b89a] to-[#8a7354]",
    "oak": "bg-gradient-to-br from-[#c4a574] via-[#8b6914] to-[#3d2914]",
    "wool": "bg-gradient-to-br from-[#d4c4b0] via-[#9a8470] to-[#5c4033]",
    "clay": "bg-gradient-to-br from-[#c9a882] via-[#a67c52] to-[#6b4423]",
}

_INK = {
    "linen": "text-[#3d2914]",
    "oak": "text-[#faf6f0]",
    "wool": "text-[#faf6f0]",
    "clay": "text-[#faf6f0]",
}


class Lightbox(Component):
    """Media viewer. Slide identity is a named MorphState key.

    ``SLIDES`` is ``(key, kicker, title, body)``. Override on the copy.
    Swipe lives on Prev / Next, not the root.
    """

    id = "lightbox"

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
    class_lede = (
        "m-0 max-w-[38ch] text-[0.9375rem] leading-relaxed text-stone-500 "
        "dark:text-stone-400"
    )
    class_hero = (
        "flex min-h-[17.5rem] cursor-pointer flex-col justify-end rounded-[1.4rem] "
        "border-0 px-6 py-6 text-left transition duration-300 "
        "hover:brightness-[1.03] active:scale-[0.995] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/20 "
        "motion-reduce:transition-none"
    )
    class_hero_idx = "font-mono text-[0.7rem] tracking-[0.18em] opacity-70"
    class_hero_title = (
        "m-0 mt-2 font-serif text-[1.65rem] font-light leading-none tracking-[-0.02em]"
    )
    class_hero_body = "m-0 mt-2 max-w-[22ch] text-[0.8rem] leading-snug opacity-80"
    class_thumbs = "grid grid-cols-4 gap-2.5"
    class_thumb = (
        "flex min-h-16 cursor-pointer flex-col justify-end rounded-[1.05rem] border-0 "
        "px-2.5 py-2 text-left transition-all duration-200 "
        "hover:brightness-[1.04] active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/20 "
        "motion-reduce:transition-none"
    )
    class_thumb_on = (
        "ring-[3px] ring-stone-900 ring-offset-2 ring-offset-[#fdfcf8] "
        "dark:ring-stone-100 dark:ring-offset-[#141311]"
    )
    class_thumb_off = "opacity-[0.72] hover:opacity-100"
    class_thumb_kicker = "font-mono text-[0.62rem] tracking-[0.14em] opacity-75"
    class_thumb_title = "m-0 mt-0.5 text-[0.72rem] font-medium leading-tight"
    class_scrim = (
        "fixed inset-0 z-40 cursor-pointer border-0 bg-stone-950/80 backdrop-blur-[2px]"
    )
    class_stage = (
        "pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-5"
    )
    class_panel = (
        "pointer-events-auto relative flex w-[min(36rem,calc(100vw-2rem))] "
        "flex-col overflow-hidden rounded-[1.6rem] bg-[#f7f4ee] text-stone-900 "
        "shadow-[0_40px_100px_-20px_rgba(0,0,0,0.55)]"
    )
    class_wash = "relative flex h-80 flex-col justify-end px-7 pb-7 pt-16"
    class_panel_idx = "font-mono text-[0.68rem] tracking-[0.2em] opacity-70"
    class_panel_kicker = "text-[0.6875rem] font-medium uppercase tracking-[0.22em] opacity-70"
    class_panel_title = (
        "m-0 mt-1 font-serif text-[2.15rem] font-light tracking-[-0.03em]"
    )
    class_panel_body = "m-0 mt-2 max-w-sm text-[0.95rem] leading-relaxed opacity-85"
    class_nav = (
        "absolute top-1/2 z-10 inline-flex size-11 -translate-y-1/2 cursor-pointer "
        "items-center justify-center rounded-full border-0 bg-white/90 text-stone-900 "
        "shadow-sm backdrop-blur-sm hover:bg-white "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
    )
    class_nav_prev = "left-3"
    class_nav_next = "right-3"
    class_close = (
        "absolute right-3 top-3 z-10 inline-flex size-11 cursor-pointer items-center "
        "justify-center rounded-full border-0 bg-white/85 text-sm font-medium "
        "text-stone-800 shadow-sm backdrop-blur-sm hover:bg-white "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
    )
    class_sr = "sr-only"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-900 px-5 text-sm font-medium text-stone-50 "
        "transition hover:bg-stone-800 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-white"
    )

    SLIDES = (
        ("linen", "Cloth", "Linen in raking light", "Cut to the shoulder. One wash, then air."),
        ("oak", "Wood", "Oak end-grain", "Wax, then rest. The grain keeps the day."),
        ("wool", "Cloth", "Wool nap", "Winter weight. Fold once, never hang."),
        ("clay", "Earth", "Clay lip", "Brush, never soak. The lip is the work."),
    )

    open = MorphState(False)
    slide = MorphState("linen")

    def on_open(self, key: str) -> str:
        return key

    def _slides(self):
        return tuple(self.SLIDES)

    def _current(self):
        rows = self._slides()
        keys = [row[0] for row in rows]
        cur = str(self.slide or keys[0])
        if cur not in keys:
            cur = keys[0]
        return keys.index(cur), cur, rows, keys

    def _wash(self, key: str) -> str:
        return _WASH.get(key, "bg-stone-800")

    def _ink(self, key: str) -> str:
        return _INK.get(key, "text-stone-50")

    def _idx(self, i: int, n: int) -> str:
        return f"{i + 1:02d}  /  {n:02d}"

    def _resting(self):
        idx, cur, rows, _keys = self._current()
        n = len(rows)
        _k, kicker, title, body = rows[idx]
        thumbs = []
        for i, (key, _kick, t, _body) in enumerate(rows):
            on = key == cur
            thumbs.append(
                button(
                    span(f"{i + 1:02d}", className=self.class_thumb_kicker),
                    span(t.split()[0], className=self.class_thumb_title),
                    type="button",
                    id=f"{self.id}-thumb-{key}",
                    className=(
                        f"{self.class_thumb} {self._wash(key)} {self._ink(key)} "
                        f"{self.class_thumb_on if on else self.class_thumb_off}"
                    ),
                    aria_current="true" if on else "false",
                    **bind(self.open_box, key=key),
                )
            )
        return [
            span("Viewer", className=self.class_kicker),
            h2("See the piece", className=self.class_title),
            p(
                "The slide is a name. Swipe when the overlay is open.",
                className=self.class_lede,
            ),
            button(
                span(self._idx(idx, n), className=self.class_hero_idx),
                span(kicker, className=self.class_kicker),
                h2(title, className=self.class_hero_title),
                p(body, className=self.class_hero_body),
                type="button",
                id=f"{self.id}-hero",
                className=f"{self.class_hero} {self._wash(cur)} {self._ink(cur)}",
                **bind(self.open_box, key=cur),
            ),
            div(*thumbs, className=self.class_thumbs),
            button(
                "Open viewer",
                type="button",
                className=self.class_btn_primary,
                **bind(self.open_box, key="linen"),
            ),
        ]

    def render(self):
        kids = list(self._resting())
        if bool(self.open):
            idx, cur, rows, _keys = self._current()
            n = len(rows)
            _k, kicker, title, body = rows[idx]
            kids.extend(
                [
                    button(
                        span("Close", className=self.class_sr),
                        type="button",
                        id=f"{self.id}-scrim",
                        className=self.class_scrim,
                        aria_label="Close",
                        **bind(self.close),
                    ),
                    div(
                        div(
                            button(
                                span("Close", className=self.class_sr),
                                type="button",
                                id=f"{self.id}-dismiss",
                                className=self.class_close,
                                aria_label="Close viewer",
                                **bind(self.close),
                            ),
                            button(
                                span("Previous slide", className=self.class_sr),
                                _chevron("left"),
                                type="button",
                                id=f"{self.id}-prev",
                                className=f"{self.class_nav} {self.class_nav_prev}",
                                aria_label="Previous slide",
                                data_channel_on="click swipe.right",
                                **bind(self.prev),
                            ),
                            button(
                                span("Next slide", className=self.class_sr),
                                _chevron("right"),
                                type="button",
                                id=f"{self.id}-next",
                                className=f"{self.class_nav} {self.class_nav_next}",
                                aria_label="Next slide",
                                data_channel_on="click swipe.left",
                                **bind(self.next),
                            ),
                            div(
                                span(self._idx(idx, n), className=self.class_panel_idx),
                                span(kicker, className=self.class_panel_kicker),
                                h2(
                                    title,
                                    className=self.class_panel_title,
                                    id=f"{self.id}-title",
                                ),
                                p(body, className=self.class_panel_body),
                                className=f"{self.class_wash} {self._wash(cur)} {self._ink(cur)}",
                                id=f"{self.id}-wash",
                            ),
                            id=f"{self.id}-panel",
                            className=self.class_panel,
                            role="dialog",
                            aria_modal="true",
                            aria_labelledby=f"{self.id}-title",
                        ),
                        className=self.class_stage,
                    ),
                ]
            )
        return div(
            *kids,
            id=self.id,
            className=self.class_card,
            data_open="1" if bool(self.open) else "0",
            data_slide=str(self.slide or "linen"),
            data_channel_id=self.id,
        )

    @action(caps=())
    def open_box(self, key: str = "", index: str = ""):
        keys = [row[0] for row in self._slides()]
        if key in keys:
            self.slide = key
        elif index != "":
            try:
                self.slide = keys[int(index) % len(keys)]
            except (TypeError, ValueError):
                self.slide = keys[0]
        elif str(self.slide or "") not in keys:
            self.slide = keys[0]
        self.open = True
        return update_with(
            self, _open_plan(self.id), extra_ops=[notify(self.on_open(str(self.slide)))]
        )

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=())
    def next(self):
        _idx, _cur, _rows, keys = self._current()
        self.slide = keys[(_idx + 1) % len(keys)]
        return update_with(self, extra_ops=[notify(str(self.slide))])

    @action(caps=())
    def prev(self):
        _idx, _cur, _rows, keys = self._current()
        self.slide = keys[(_idx - 1) % len(keys)]
        return update_with(self, extra_ops=[notify(str(self.slide))])
