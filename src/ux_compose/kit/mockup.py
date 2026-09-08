"""Drop-in mockup — named device frame around a preview.

Host seam: override ``PREVIEW``. Choosing a device is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. Caps: none. A11y: device radiogroup; frame labelled.
Not Hero (landing CTA).
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


class Mockup(Component):
    """How it sits on a desk or a phone. The device is a name."""

    id = "mockup"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_frame = "mx-auto flex items-center justify-center rounded-[1.75rem] border-8 border-stone-900 bg-stone-50 p-6 text-sm"

    DEVICES = (("desk", "Desk"), ("phone", "Phone"), ("tile", "Tile"))
    PREVIEW = "Quiet pieces for a working house."
    value = MorphState("desk")

    def render(self):
        val = str(self.value or "desk")
        width = {"desk": "w-full", "phone": "w-40", "tile": "w-52"}.get(val, "w-full")
        chips = [
            button(
                lab,
                type="button",
                role="radio",
                aria_checked="true" if key == val else "false",
                className="rounded-full px-3 py-2 text-xs " + ("bg-stone-900 text-stone-50" if key == val else "bg-stone-100"),
                **bind(self.choose, key=key),
            )
            for key, lab in self.DEVICES
        ]
        return div(
            span("Look", className=self.class_kicker),
            h2("On the table", className=self.class_title),
            p("A named frame. Choosing is public.", className=self.class_lede),
            div(*chips, className="flex gap-2", role="radiogroup", aria_label="Device"),
            div(self.PREVIEW, className=f"{self.class_frame} {width}", aria_label=f"{val} preview"),
            id=self.id,
            className=self.class_card,
            data_value=val,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {k for k, _ in self.DEVICES}
        self.value = key if key in keys else "desk"
        return update_with(self, extra_ops=[notify(str(self.value))])
