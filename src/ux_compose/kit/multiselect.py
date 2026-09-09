"""Drop-in multi-select — named set on RefState, listbox.

Host seam: render slots OR subclass.
Accepted: ``options`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``, ``dirty``. RefState: ``selected``. Caps: none.
A11y (APG Listbox multi): trigger ``aria-haspopup=listbox``; options
``aria-selected``. Escape on scrim. Header select-all is a distinct action.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
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
    p,
    span,
)


class MultiSelect(Component):
    """Several named values. The set is RefState; open is MorphState."""

    id = "multiselect"
    _SEAMS = {'options': 'OPTIONS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_wrap = "relative z-20 max-w-80"
    class_trigger = (
        "flex min-h-11 w-full cursor-pointer items-center justify-between rounded-2xl "
        "border border-stone-200 bg-stone-50 px-4 text-sm"
    )
    class_menu = (
        "absolute left-0 right-0 top-[calc(100%+0.35rem)] z-30 flex flex-col "
        "rounded-2xl border border-stone-200 bg-white p-1.5 shadow-lg"
    )
    class_option = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-transparent "
        "px-3.5 text-left text-sm hover:bg-stone-100"
    )
    class_option_on = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-stone-100 "
        "px-3.5 text-left text-sm"
    )
    class_all = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-transparent "
        "px-3.5 text-left text-xs font-medium uppercase tracking-widest text-stone-400"
    )
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"

    OPTIONS = (("linen", "Linen"), ("oak", "Oak"), ("wool", "Wool"), ("clay", "Clay"))

    open = MorphState(False)
    selected = RefState(("linen",))
    dirty = MorphState("idle")

    def _options(self):
        return tuple(self.OPTIONS)

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        sel = set(self.selected or ())
        is_open = bool(self.open)
        shown = ", ".join(lab for k, lab in self._options() if k in sel) or "Choose materials"
        rows = []
        if is_open:
            all_on = {k for k, _ in self._options()} <= sel
            rows.append(
                button(
                    "Clear all" if all_on else "Select all",
                    type="button",
                    className=self.class_all,
                    **bind(self.toggle_all),
                )
            )
            for key, lab in self._options():
                on = key in sel
                rows.append(
                    button(
                        lab,
                        type="button",
                        role="option",
                        aria_selected="true" if on else "false",
                        className=self.class_option_on if on else self.class_option,
                        **bind(self.toggle, key=key),
                    )
                )
        menu = (
            div(*rows, id=f"{self.id}-list", className=self.class_menu, role="listbox", aria_multiselectable="true")
            if is_open else span("", className=self.class_sr)
        )
        scrim = (
            button(
                span("Close", className=self.class_sr),
                type="button",
                className=self.class_scrim,
                aria_label="Close",
                data_channel_on="click keydown.escape",
                **bind(self.close),
            )
            if is_open else span("", className=self.class_sr)
        )
        return kit_shell(self,
            scrim,
            div(
                button(
                    shown,
                    type="button",
                    id=f"{self.id}-trigger",
                    className=self.class_trigger,
                    aria_haspopup="listbox",
                    aria_expanded="true" if is_open else "false",
                    aria_controls=f"{self.id}-list",
                    **bind(self.toggle_open),
                ),
                menu,
                className=self.class_wrap,
            ),
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
            chrome=(
                span("Field", className=self.class_kicker),
                h2("Materials", className=self.class_title),
                p("Several names. Select-all is not a row click.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def toggle_open(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=())
    def toggle(self, key: str = ""):
        keys = {k for k, _ in self._options()}
        cur = set(self.selected or ())
        if key in cur:
            cur.remove(key)
        elif key in keys:
            cur.add(key)
        self.selected = tuple(sorted(cur))
        self._mark()
        return update_with(self, extra_ops=[notify(key)])

    @action(caps=())
    def toggle_all(self):
        known = {k for k, _ in self._options()}
        cur = set(self.selected or ())
        self.selected = () if known <= cur else tuple(sorted(known))
        self._mark()
        return update_with(self)
