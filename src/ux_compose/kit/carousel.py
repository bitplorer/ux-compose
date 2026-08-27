"""Drop-in carousel — named slides, never a quantity MorphState.

Host seam: override ``SLIDES``. Prev / next compute the neighbor key.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

Live: the root ``id`` is the region. Channel picks it up.
Host ``swipe.horizontal``. Prev accepts ``click swipe.right``,
Next accepts ``click swipe.left`` — same synthesizer as PullRefresh,
no extra JS and no second attribute family.
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
    span,
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
        "[grid-area:card] self-start relative mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 overflow-x-hidden "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 max-w-sm text-sm leading-relaxed text-stone-500"
    class_stage = (
        "flex min-h-48 touch-pan-y select-none flex-col justify-end gap-3 "
        "rounded-2xl bg-stone-50 px-6 py-6"
    )
    class_index = "font-serif text-5xl font-medium tracking-tight text-stone-200"
    class_bar = "flex min-w-0 flex-wrap items-center justify-between gap-2"
    class_dots = "flex min-w-0 flex-wrap items-center justify-center"
    class_dot = (
        "inline-flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent p-0"
    )
    class_pip = "pointer-events-none block h-2.5 w-2.5 rounded-full bg-stone-200"
    class_pip_on = "pointer-events-none block h-2.5 w-6 rounded-full bg-stone-800"
    class_btn_ghost = (
        "inline-flex min-h-11 shrink-0 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-4 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )

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

    def render(self):
        idx, cur, rows, keys = self._current()
        key, kicker, title, body = rows[idx]
        n = len(keys)
        dots = [
            button(
                span(lab, className="sr-only"),
                span("", className=self.class_pip_on if k == cur else self.class_pip),
                type="button",
                className=self.class_dot,
                aria_label=lab,
                aria_current="true" if k == cur else "false",
                **bind(self.goto, key=k),
            )
            for k, lab, _t, _b in rows
        ]
        return div(
            div(
                span(f"{idx + 1:02d}", className=self.class_index),
                span(kicker, className=self.class_kicker),
                h2(title, className=self.class_title),
                p(body, className=self.class_lede),
                className=self.class_stage,
            ),
            div(
                button(
                    "Prev",
                    type="button",
                    className=self.class_btn_ghost,
                    data_channel_on="click swipe.right",
                    **bind(self.prev),
                ),
                div(*dots, className=self.class_dots, role="tablist"),
                button(
                    "Next",
                    type="button",
                    className=self.class_btn_ghost,
                    data_channel_on="click swipe.left",
                    **bind(self.next),
                ),
                className=self.class_bar,
            ),
            id=self.id,
            className=self.class_card,
            data_slide=cur,
            data_of=str(n),
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
