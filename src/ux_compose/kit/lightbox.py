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
    "linen": "bg-gradient-to-br from-stone-200 via-amber-100 to-stone-400",
    "oak": "bg-gradient-to-br from-amber-800 via-stone-700 to-stone-900",
    "wool": "bg-gradient-to-br from-stone-400 via-stone-600 to-stone-800",
    "clay": "bg-gradient-to-br from-rose-300 via-amber-200 to-stone-500",
}


class Lightbox(Component):
    """Media viewer. Slide identity is a named MorphState key.

    ``SLIDES`` is ``(key, kicker, title, body)``. Override on the copy.
    Swipe lives on Prev / Next, not the root.
    """

    id = "lightbox"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 "
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
    class_thumbs = "grid grid-cols-2 gap-2"
    class_thumb = (
        "flex min-h-28 cursor-pointer flex-col justify-end overflow-hidden rounded-2xl "
        "border-0 px-4 py-3 text-left text-stone-50 shadow-inner transition "
        "hover:-translate-y-0.5 hover:shadow active:scale-[0.99] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/20"
    )
    class_thumb_kicker = "text-xs uppercase tracking-widest text-white/70"
    class_thumb_title = "m-0 font-serif text-lg font-medium tracking-tight"
    class_scrim = "fixed inset-0 z-40 cursor-pointer border-0 bg-stone-900/70"
    class_stage = (
        "pointer-events-none fixed inset-0 z-50 flex items-center justify-center p-4"
    )
    class_panel = (
        "pointer-events-auto relative flex w-[min(36rem,calc(100vw-2rem))] "
        "flex-col overflow-hidden rounded-[1.75rem] bg-stone-950 text-stone-50 shadow-2xl"
    )
    class_wash = "relative flex h-64 flex-col justify-end px-6 pb-6 pt-16"
    class_panel_kicker = "text-xs uppercase tracking-widest text-white/70"
    class_panel_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_panel_body = "m-0 mt-2 max-w-sm text-sm leading-relaxed text-white/80"
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
        "justify-center rounded-full border-0 bg-stone-900/50 text-sm font-medium "
        "text-stone-50 hover:bg-stone-900/70 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/40"
    )
    class_sr = "sr-only"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 "
        "hover:bg-stone-700 active:scale-[0.98] "
        "dark:bg-stone-200 dark:text-stone-900 dark:hover:bg-white"
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

    def _resting(self):
        thumbs = []
        for key, kicker, title, _body in self._slides():
            thumbs.append(
                button(
                    span(kicker, className=self.class_thumb_kicker),
                    span(title, className=self.class_thumb_title),
                    type="button",
                    id=f"{self.id}-thumb-{key}",
                    className=f"{self.class_thumb} {self._wash(key)}",
                    **bind(self.open_box, key=key),
                )
            )
        return [
            span("Viewer", className=self.class_kicker),
            h2("See the piece", className=self.class_title),
            p("The slide is a name. Swipe when the overlay is open.", className=self.class_lede),
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
                                span(kicker, className=self.class_panel_kicker),
                                h2(title, className=self.class_panel_title, id=f"{self.id}-title"),
                                p(body, className=self.class_panel_body),
                                className=f"{self.class_wash} {self._wash(cur)}",
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
        return update_with(self, _open_plan(self.id), extra_ops=[notify(self.on_open(str(self.slide)))])

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
