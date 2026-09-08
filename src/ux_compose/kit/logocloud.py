"""Drop-in logo cloud — named marks, public choose.

Host seam: override ``LOGOS``. Choosing is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. Caps: none. A11y: list of buttons; each ``img`` has
``alt``; selected ``aria-pressed``. Not Avatar (initials).
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
    img,
    p,
    span,
)


class LogoCloud(Component):
    """Houses we keep. The selected mark is a name.

    ``LOGOS`` is ``(key, label, src)``. Override on the copy.
    """

    id = "logocloud"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_row = "flex flex-wrap gap-2"
    class_btn = (
        "inline-flex min-h-14 min-w-14 cursor-pointer flex-col items-center justify-center "
        "gap-1 rounded-2xl border border-stone-200 bg-stone-50 px-3 py-2 text-xs"
    )
    class_btn_on = (
        "inline-flex min-h-14 min-w-14 cursor-pointer flex-col items-center justify-center "
        "gap-1 rounded-2xl border-0 bg-stone-900 px-3 py-2 text-xs text-stone-50"
    )
    class_img = "h-8 w-8 rounded-full object-cover"

    LOGOS = (
        ("linen", "Linen mill", "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"),
        ("oak", "Oak workshop", "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"),
        ("wool", "Wool loft", "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"),
        ("clay", "Clay studio", "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"),
    )

    value = MorphState("linen")

    def _logos(self):
        return tuple(self.LOGOS)

    def render(self):
        val = str(self.value or self._logos()[0][0])
        keys = {row[0] for row in self._logos()}
        if val not in keys:
            val = self._logos()[0][0]
        marks = []
        for key, lab, src in self._logos():
            on = key == val
            marks.append(
                button(
                    img(src=src, alt=lab, className=self.class_img),
                    span(lab),
                    type="button",
                    className=self.class_btn_on if on else self.class_btn,
                    aria_pressed="true" if on else "false",
                    aria_label=lab,
                    **bind(self.choose, key=key),
                )
            )
        return div(
            span("Houses", className=self.class_kicker),
            h2("Who we keep", className=self.class_title),
            p("Named marks. Choosing is public.", className=self.class_lede),
            div(*marks, className=self.class_row, role="list", aria_label="Houses"),
            id=self.id,
            className=self.class_card,
            data_value=val,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._logos()}
        self.value = key if key in keys else self._logos()[0][0]
        return update_with(self, extra_ops=[notify(str(self.value))])
