"""Drop-in select — grouped options, placeholder, click-away scrim.

Host seam: override ``GROUPS``. Distinct from Dropdown: a form field with groups.
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


class Select(Component):
    """Closed trigger, grouped list. Value is a named key.

    ``GROUPS`` is ``(label, ((key, option), …))``. Override on the copy.
    """

    id = "select"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_wrap = "relative z-20 max-w-80"
    class_trigger = (
        "flex min-h-11 w-full cursor-pointer items-center justify-between gap-4 "
        "rounded-2xl border border-stone-200 bg-stone-50 px-4 text-sm text-inherit"
    )
    class_trigger_open = (
        "flex min-h-11 w-full cursor-pointer items-center justify-between gap-4 "
        "rounded-2xl border border-stone-400 bg-white px-4 text-sm text-inherit"
    )
    class_ph = "text-stone-400"
    class_menu = (
        "absolute left-0 right-0 top-[calc(100%+0.35rem)] z-30 flex max-h-72 "
        "flex-col overflow-auto rounded-2xl border border-stone-200 bg-white p-1.5 shadow-lg"
    )
    class_group = "px-3 pt-2 pb-1 text-xs font-medium uppercase tracking-widest text-stone-400"
    class_option = (
        "flex min-h-11 cursor-pointer items-center justify-between rounded-xl "
        "border-0 bg-transparent px-3.5 text-left text-sm hover:bg-stone-100"
    )
    class_option_on = (
        "flex min-h-11 cursor-pointer items-center justify-between rounded-xl "
        "border-0 bg-stone-100 px-3.5 text-left text-sm"
    )
    class_check = "text-xs font-medium text-stone-500"
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"
    class_caret = "inline-block text-stone-400 transition-transform"

    GROUPS = (
        ("Cloth", (("linen", "Linen"), ("wool", "Wool"))),
        ("Wood", (("oak", "Oak"), ("ash", "Ash"))),
        ("Earth", (("clay", "Clay"), ("stone", "Stone"))),
    )

    open = MorphState(False)
    value = MorphState("")

    def _groups(self):
        return tuple(self.GROUPS)

    def _options(self):
        rows = []
        for _g, opts in self._groups():
            rows.extend(opts)
        return tuple(rows)

    def _label(self, key: str) -> str:
        for k, lab in self._options():
            if k == key:
                return lab
        return ""

    def render(self):
        val = str(self.value or "")
        shown = self._label(val) or "Choose a material"
        is_open = bool(self.open)
        menu_kids = []
        if is_open:
            for group, opts in self._groups():
                menu_kids.append(span(group, className=self.class_group))
                for key, lab in opts:
                    on = key == val
                    menu_kids.append(
                        button(
                            span(lab),
                            span("Selected" if on else "", className=self.class_check if on else self.class_sr),
                            type="button",
                            role="option",
                            aria_selected="true" if on else "false",
                            className=self.class_option_on if on else self.class_option,
                            **bind(self.choose, key=key),
                        )
                    )
        menu = (
            div(*menu_kids, className=self.class_menu, role="listbox")
            if is_open
            else span("", className=self.class_sr)
        )
        scrim = (
            button(
                span("Close", className=self.class_sr),
                type="button",
                className=self.class_scrim,
                aria_label="Close",
                **bind(self.toggle),
            )
            if is_open
            else span("", className=self.class_sr)
        )
        return div(
            span("Field", className=self.class_kicker),
            h2("Material", className=self.class_title),
            p("Grouped options. The value is a name.", className=self.class_lede),
            span("Finish", className=self.class_label),
            scrim,
            div(
                button(
                    span(shown, className="" if val else self.class_ph),
                    span("▾", className=self.class_caret + (" rotate-180" if is_open else ""), aria_hidden="true"),
                    type="button",
                    className=self.class_trigger_open if is_open else self.class_trigger,
                    aria_expanded="true" if is_open else "false",
                    aria_haspopup="listbox",
                    **bind(self.toggle),
                ),
                menu,
                className=self.class_wrap,
            ),
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
            data_value=val,
        )

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {k for k, _ in self._options()}
        if key in keys:
            self.value = key
        self.open = False
        return update_with(self, extra_ops=[notify(self._label(str(self.value)) or str(self.value))])
