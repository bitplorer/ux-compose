"""Drop-in timeline — named filter, events silent.

Host seam: override ``LANES`` / ``EVENTS``. Filtering is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    h3,
    p,
    span,
)


class Timeline(Component):
    """Ordered history. Filter is a lane name, never an index.

    ``LANES`` is ``(key, label)``. ``EVENTS`` is ``(key, title, body, when)``.
    Empty lane is a first-class row.
    """

    id = "timeline"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-6 "
        "overflow-x-hidden rounded-[1.85rem] border border-stone-900/[0.07] bg-[#fdfcf8] p-7 text-stone-900 "
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
    class_lede = "m-0 max-w-[36ch] text-[0.9375rem] leading-relaxed text-stone-500 dark:text-stone-400"
    class_seg = (
        "flex min-w-0 flex-wrap gap-0.5 rounded-full bg-stone-900/[0.05] p-1 "
        "dark:bg-white/5"
    )
    class_chip = (
        "min-h-10 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-transparent px-3.5 text-[0.8125rem] font-medium text-stone-500 "
        "transition hover:text-stone-900 focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:text-stone-400 dark:hover:text-stone-50"
    )
    class_chip_on = (
        "min-h-10 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-white px-3.5 text-[0.8125rem] font-medium text-stone-900 shadow-sm "
        "ring-1 ring-stone-900/5 focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-800 dark:text-stone-50 dark:ring-white/10"
    )
    class_rail = "relative flex flex-col gap-0 pl-0.5"
    class_row = "relative flex gap-4 py-3.5"
    class_dot = (
        "relative z-[1] mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full "
        "bg-stone-400 ring-[3px] ring-[#fdfcf8] dark:bg-stone-500 dark:ring-[#141311]"
    )
    class_dot_cut = (
        "relative z-[1] mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full "
        "bg-amber-600 ring-[3px] ring-[#fdfcf8] dark:bg-amber-400 dark:ring-[#141311]"
    )
    class_dot_make = (
        "relative z-[1] mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full "
        "bg-sky-700 ring-[3px] ring-[#fdfcf8] dark:bg-sky-400 dark:ring-[#141311]"
    )
    class_dot_keep = (
        "relative z-[1] mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full "
        "bg-emerald-700 ring-[3px] ring-[#fdfcf8] dark:bg-emerald-400 dark:ring-[#141311]"
    )
    class_line = (
        "absolute bottom-3 left-[0.28rem] top-3 w-px bg-stone-200 "
        "dark:bg-stone-800"
    )
    class_event = "flex min-w-0 flex-1 flex-col gap-0.5"
    class_event_head = "flex items-baseline justify-between gap-3"
    class_event_title = "m-0 font-serif text-[1.05rem] font-medium tracking-tight"
    class_event_body = "m-0 text-[0.875rem] leading-relaxed text-stone-500 dark:text-stone-400"
    class_when = (
        "m-0 shrink-0 text-[0.6875rem] font-medium uppercase tracking-[0.16em] "
        "text-stone-400 dark:text-stone-500"
    )
    class_lane_mark = (
        "mt-1.5 inline-flex w-fit rounded-full bg-stone-900/[0.05] px-2 py-0.5 "
        "text-[0.625rem] font-semibold uppercase tracking-[0.14em] text-stone-500 "
        "dark:bg-white/5 dark:text-stone-400"
    )
    class_empty = (
        "rounded-2xl bg-white/60 px-5 py-10 text-center text-sm text-stone-500 "
        "ring-1 ring-dashed ring-stone-300 dark:bg-stone-900/40 dark:text-stone-400 "
        "dark:ring-stone-700"
    )

    LANES = (
        ("all", "All"),
        ("cut", "Cut"),
        ("make", "Make"),
        ("keep", "Keep"),
    )
    EVENTS = (
        ("cut", "Shirt marked", "The shoulder is the work.", "Morning"),
        ("make", "Board oiled", "Wax, then rest.", "Midday"),
        ("keep", "Throw folded", "Once, never hung.", "Dusk"),
        ("cut", "Second shirt", "Same cut, quieter cloth.", "Night"),
    )

    filt = MorphState("all")
    events = RefState(EVENTS)
    stamp = MorphState("idle")

    def _lanes(self):
        return tuple(self.LANES)

    def _events(self):
        return tuple(self.events or self.EVENTS)

    def _dot(self, key: str):
        return {
            "cut": self.class_dot_cut,
            "make": self.class_dot_make,
            "keep": self.class_dot_keep,
        }.get(key, self.class_dot)

    def render(self):
        f = str(self.filt or "all")
        lanes = self._lanes()
        keys = {row[0] for row in lanes}
        if f not in keys:
            f = "all"
        rows = [e for e in self._events() if f == "all" or e[0] == f]
        segs = [
            button(
                lab,
                type="button",
                className=self.class_chip_on if key == f else self.class_chip,
                aria_pressed="true" if key == f else "false",
                **bind(self.filter, key=key),
            )
            for key, lab in lanes
        ]
        items = []
        if not rows:
            items.append(
                p("Nothing in this lane.", className=self.class_empty, id=f"{self.id}-empty")
            )
        else:
            events = []
            for i, (kind, title, body, when) in enumerate(rows):
                events.append(
                    div(
                        span("", className=self._dot(kind), aria_hidden="true"),
                        div(
                            div(
                                h3(title, className=self.class_event_title),
                                p(when, className=self.class_when),
                                className=self.class_event_head,
                            ),
                            p(body, className=self.class_event_body),
                            span(kind, className=self.class_lane_mark),
                            className=self.class_event,
                        ),
                        id=f"{self.id}-e-{i}",
                        className=self.class_row,
                    )
                )
            items.append(
                div(
                    span("", className=self.class_line, aria_hidden="true"),
                    *events,
                    id=f"{self.id}-rail",
                    className=self.class_rail,
                )
            )
        return div(
            span("Log", className=self.class_kicker),
            h2("The day's work", className=self.class_title),
            p("Filter is a name. The empty lane is a row, not a blank stage.", className=self.class_lede),
            div(*segs, className=self.class_seg, role="tablist"),
            *items,
            id=self.id,
            className=self.class_card,
            data_filt=f,
        )

    @action(caps=())
    def filter(self, key: str = "all"):
        keys = {row[0] for row in self._lanes()}
        self.filt = key if key in keys else "all"
        return update_with(self, extra_ops=[notify(str(self.filt))])
