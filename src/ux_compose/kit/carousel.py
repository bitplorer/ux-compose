"""Drop-in carousel — named slides, never a quantity MorphState.

Host seam: override ``SLIDES``. Prev / next compute the neighbor key.
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
    span,
)


class Carousel(Component):
    """One named slide at a time.

    ``SLIDES`` is ``(key, kicker, title, body)``. Override on the copy.
    """

    id = "carousel"

    class_card = (
        "relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 max-w-sm text-sm leading-relaxed text-stone-500"
    class_stage = (
        "flex min-h-48 flex-col justify-end gap-3 rounded-2xl bg-stone-50 px-6 py-6"
    )
    class_index = "font-serif text-5xl font-medium tracking-tight text-stone-200"
    class_bar = "flex items-center justify-between gap-3"
    class_dots = "flex gap-1.5"
    class_dot = (
        "h-2.5 w-2.5 cursor-pointer rounded-full border-0 bg-stone-200 p-0"
    )
    class_dot_on = (
        "h-2.5 w-6 cursor-pointer rounded-full border-0 bg-stone-800 p-0"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
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
                type="button",
                className=self.class_dot_on if k == cur else self.class_dot,
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
                button("Prev", type="button", className=self.class_btn_ghost, **bind(self.prev)),
                div(*dots, className=self.class_dots),
                button("Next", type="button", className=self.class_btn_ghost, **bind(self.next)),
                className=self.class_bar,
            ),
            id=self.id,
            className=self.class_card,
            data_slide=cur,
            data_of=str(n),
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
