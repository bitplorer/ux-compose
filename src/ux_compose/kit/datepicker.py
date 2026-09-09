"""Drop-in date picker — named day + month keys, labeled field.

Host seam: construct kwargs OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``month``, ``day``, ``open``. Caps: none. A11y: label ``for`` ↔
textbox id; grid ``role=grid``; weekday row ``columnheader``; days
``role=row`` / ``gridcell``; selected day ``aria-selected``. Popover
closes on Escape. Quantity never lives on MorphState — the day is a name.
"""

from __future__ import annotations

import calendar as _cal
from datetime import datetime

from ux_compose.kit_construct import Kit
from ux_compose import (
    MorphState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    label,
    p,
    span,
)

_cal.setfirstweekday(_cal.MONDAY)
_WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


def _parse_month(raw: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(str(raw), "%Y-%m")
        return dt.year, dt.month
    except ValueError:
        return 2026, 8


def _shift(raw: str, delta: int) -> str:
    y, m = _parse_month(raw)
    m += delta
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


class DatePicker(Kit):
    """Labeled date field + month grid. Day is a named key (YYYY-MM-DD)."""

    id = "datepicker"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_input = (
        "w-full min-h-11 cursor-pointer rounded-2xl border border-stone-200 bg-stone-50 "
        "px-4 text-left text-sm"
    )
    class_grid = "mt-3 flex flex-col gap-1"
    class_row = "grid grid-cols-7 gap-1"
    class_day = (
        "min-h-11 cursor-pointer rounded-xl border-0 bg-transparent text-sm hover:bg-stone-100"
    )
    class_day_on = (
        "min-h-11 cursor-pointer rounded-xl border-0 bg-stone-900 text-sm font-medium text-stone-50"
    )
    class_head = "flex items-center justify-between"
    class_ghost = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-200 bg-white text-sm"
    )
    class_scrim = "fixed inset-0 z-10 cursor-pointer border-0 bg-transparent"
    class_sr = "sr-only"

    month = MorphState("2026-08")
    day = MorphState("2026-08-26")
    open = MorphState(False)

    def on_pick(self, day: str) -> str:
        return day

    def render(self):
        month = str(self.month or "2026-08")
        day = str(self.day or "")
        is_open = bool(self.open)
        y, m = _parse_month(month)
        field_id = f"{self.id}-day"
        kids = [
            span("When", className=self.class_kicker),
            h2("Pick a day", className=self.class_title),
            p("The day is a name. The calendar is presence.", className=self.class_lede),
            label("Date", className=self.class_label, html_for=field_id),
            button(
                day or "Choose a day",
                type="button",
                id=field_id,
                className=self.class_input,
                aria_haspopup="dialog",
                aria_expanded="true" if is_open else "false",
                aria_controls=f"{self.id}-cal",
                **bind(self.toggle),
            ),
        ]
        if is_open:
            header = [
                span(w, className="text-center text-xs text-stone-400", role="columnheader")
                for w in _WEEKDAYS
            ]
            rows = [div(*header, className=self.class_row, role="row")]
            week = []
            for d in _cal.Calendar(_cal.MONDAY).itermonthdays(y, m):
                if d == 0:
                    week.append(div(span("", className="min-h-11"), role="gridcell"))
                else:
                    key = f"{y:04d}-{m:02d}-{d:02d}"
                    on = key == day
                    week.append(
                        div(
                            button(
                                str(d),
                                type="button",
                                className=self.class_day_on if on else self.class_day,
                                aria_selected="true" if on else "false",
                                **bind(self.pick, day=key),
                            ),
                            role="gridcell",
                        )
                    )
                if len(week) == 7:
                    rows.append(div(*week, className=self.class_row, role="row"))
                    week = []
            kids.extend([
                button(
                    span("Close", className=self.class_sr),
                    type="button",
                    className=self.class_scrim,
                    aria_label="Close calendar",
                    data_channel_on="click keydown.escape",
                    **bind(self.toggle),
                ),
                div(
                    div(
                        button("‹", type="button", className=self.class_ghost, aria_label="Previous month", **bind(self.prev)),
                        span(f"{_cal.month_name[m]} {y}", className="text-sm font-medium"),
                        button("›", type="button", className=self.class_ghost, aria_label="Next month", **bind(self.next)),
                        className=self.class_head,
                    ),
                    div(*rows, className=self.class_grid, role="grid", aria_label=f"{_cal.month_name[m]} {y}"),
                    id=f"{self.id}-cal",
                    className="relative z-20 rounded-2xl border border-stone-200 bg-white p-3 shadow-lg",
                    role="dialog",
                    aria_label="Choose a date",
                ),
            ])
        return div(*kids, id=self.id, className=self.class_card, data_open="1" if is_open else "0", data_day=day)

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def prev(self):
        self.month = _shift(str(self.month or "2026-08"), -1)
        return update_with(self)

    @action(caps=())
    def next(self):
        self.month = _shift(str(self.month or "2026-08"), 1)
        return update_with(self)

    @action(caps=())
    def pick(self, day: str = ""):
        if day:
            self.day = day
            self.month = day[:7]
        self.open = False
        return update_with(self, extra_ops=[notify(self.on_pick(str(self.day)))])
