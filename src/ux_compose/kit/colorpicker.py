"""Drop-in color picker — named swatches plus a labeled hex field.

Host seam: construct kwargs OR subclass.
Accepted: ``swatches`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``value``. RefState: ``hex``, ``dirty`` clock on MorphState.
Caps: none. A11y: swatches ``role=radiogroup`` / ``radio``; label ``for``
↔ hex id. Not Badge (status chips).
"""

from __future__ import annotations

from ux_compose.kit_construct import Kit
from ux_compose import (
    MorphState,
    RefState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    input_,
    label,
    p,
    span,
)


class ColorPicker(Kit):
    """Named ink. The swatch is a key; hex is RefState."""

    id = "colorpicker"
    _SEAMS = {'swatches': 'SWATCHES'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_row = "flex flex-wrap gap-2"
    class_swatch = "inline-flex h-11 w-11 cursor-pointer items-center justify-center rounded-full border-0"
    class_label = "text-sm font-medium"
    class_input = (
        "min-h-11 w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 text-sm outline-none"
    )

    SWATCHES = (
        ("linen", "Linen", "#e7e5e4"),
        ("oak", "Oak", "#78716c"),
        ("wool", "Wool", "#a8a29e"),
        ("ink", "Ink", "#1c1917"),
    )

    value = MorphState("linen")
    hex = RefState("#e7e5e4")
    dirty = MorphState("idle")

    def _swatches(self):
        return tuple(self.SWATCHES)

    def render(self):
        val = str(self.value or "linen")
        hexv = str(self.hex or "#e7e5e4")
        fid = f"{self.id}-hex"
        title_id = f"{self.id}-label"
        chips = []
        for key, lab, color in self._swatches():
            on = key == val
            chips.append(
                button(
                    span("", className="sr-only"),
                    type="button",
                    role="radio",
                    aria_checked="true" if on else "false",
                    aria_label=lab,
                    className=self.class_swatch + (" ring-2 ring-stone-900 ring-offset-2" if on else ""),
                    style=f"background:{color}",
                    **bind(self.choose, key=key),
                )
            )
        return self.kit_shell(
            span("Ink", className=self.class_kicker),
            h2("Color", id=title_id, className=self.class_title),
            p("A named swatch. Hex attaches.", className=self.class_lede),
            div(*chips, className=self.class_row, role="radiogroup", aria_labelledby=title_id),
            label("Hex", className=self.class_label, html_for=fid),
            input_(
                type="text",
                name="hex",
                id=fid,
                value=hexv,
                className=self.class_input,
                **bind(self.set_field, field="hex"),
            ),
            id=self.id,
            className=self.class_card,
            data_value=val,
        )

    @action(caps=())
    def choose(self, key: str = ""):
        for k, _lab, color in self._swatches():
            if k == key:
                self.value = key
                self.hex = color
                self.dirty = "b" if self.dirty == "a" else "a"
                return update_with(self, extra_ops=[notify(key)])
        self.value = self._swatches()[0][0]
        return update_with(self)

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("hex", ""))
        self.hex = "" if raw is None else str(raw)
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self)
