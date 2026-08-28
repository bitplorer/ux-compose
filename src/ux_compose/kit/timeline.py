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
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-5 "
        "overflow-x-hidden rounded-[1.75rem] border border-stone-200/90 bg-white p-6 text-stone-900 "
        "shadow-[0_1px_0_rgba(22,21,19,0.04),0_24px_48px_-28px_rgba(22,21,19,0.4)] "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-xs font-medium uppercase tracking-[0.2em] text-stone-500 "
        "dark:text-stone-400"
    )
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_seg = (
        "flex min-w-0 flex-wrap gap-1 rounded-full bg-stone-100 p-1 "
        "dark:bg-stone-900"
    )
    class_chip = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-transparent px-4 text-sm font-medium text-stone-500 "
        "hover:text-stone-900 focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:text-stone-400 dark:hover:text-stone-50"
    )
    class_chip_on = (
        "min-h-11 flex-1 cursor-pointer whitespace-nowrap rounded-full border-0 "
        "bg-white px-4 text-sm font-medium text-stone-900 shadow-sm "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-800 dark:text-stone-50"
    )
    class_rail = "relative flex flex-col gap-0 pl-1"
    class_row = "relative flex gap-4 py-3"
    class_dot = (
        "relative z-[1] mt-1.5 h-3 w-3 shrink-0 rounded-full border-2 "
        "border-stone-900 bg-white dark:border-stone-100 dark:bg-stone-950"
    )
    class_dot_cut = (
        "relative z-[1] mt-1.5 h-3 w-3 shrink-0 rounded-full border-2 "
        "border-amber-700 bg-amber-200 dark:border-amber-400 dark:bg-amber-900"
    )
    class_dot_make = (
        "relative z-[1] mt-1.5 h-3 w-3 shrink-0 rounded-full border-2 "
        "border-sky-800 bg-sky-200 dark:border-sky-400 dark:bg-sky-900"
    )
    class_dot_keep = (
        "relative z-[1] mt-1.5 h-3 w-3 shrink-0 rounded-full border-2 "
        "border-emerald-800 bg-emerald-200 dark:border-emerald-400 dark:bg-emerald-900"
    )
    class_line = (
        "absolute bottom-0 left-[0.35rem] top-0 w-px bg-stone-200 "
        "dark:bg-stone-800"
    )
    class_event_title = "m-0 font-serif text-lg font-medium tracking-tight"
    class_event_body = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_when = "m-0 text-xs uppercase tracking-widest text-stone-400"
    class_empty = (
        "rounded-2xl bg-stone-50 px-5 py-8 text-center text-sm text-stone-500 "
        "dark:bg-stone-900 dark:text-stone-400"
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
                            p(when, className=self.class_when),
                            h3(title, className=self.class_event_title),
                            p(body, className=self.class_event_body),
                            className="flex min-w-0 flex-col gap-1",
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
