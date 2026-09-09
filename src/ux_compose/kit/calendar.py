"""Drop-in calendar — month and day are named keys.

Host seam: render slots OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``month``, ``day``. Caps: none. A11y (APG Date Picker grid):
``role=grid``; weekday ``role=columnheader``; days ``role=row`` /
``gridcell``; selected day ``aria-selected``.
Picking a day is public.
"""

from __future__ import annotations

import calendar as _cal
from datetime import datetime

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
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


_cal.setfirstweekday(_cal.MONDAY)
_WEEKDAYS = ("Mo", "Tu", "We", "Th", "Fr", "Sa", "Su")


def _parse_month(raw: str) -> tuple[int, int]:
    try:
        dt = datetime.strptime(str(raw), "%Y-%m")
        return dt.year, dt.month
    except ValueError:
        return 2026, 8


def _shift_month(raw: str, delta: int) -> str:
    y, m = _parse_month(raw)
    m += delta
    while m > 12:
        m -= 12
        y += 1
    while m < 1:
        m += 12
        y -= 1
    return f"{y:04d}-{m:02d}"


class Calendar(Component):
    """Month grid. ``month`` is ``YYYY-MM``. ``day`` is ``YYYY-MM-DD``.

    Prev / next shift the month key on the server. Picking a day is public.
    """

    id = "calendar"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full min-w-0 max-w-xl flex-col gap-4 overflow-x-hidden "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 min-w-0 flex-1 text-center font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_head = "flex min-w-0 flex-wrap items-center justify-between gap-2"
    class_btn_ghost = (
        "inline-flex min-h-11 min-w-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-200 bg-white px-4 text-sm font-medium "
        "text-stone-900 hover:bg-stone-100"
    )
    class_grid = "flex flex-col gap-1"
    class_row = "grid grid-cols-7 gap-1"
    class_dow = "py-2 text-center text-xs font-medium uppercase tracking-widest text-stone-400"
    class_empty = "min-h-11"
    class_day = (
        "min-h-11 cursor-pointer rounded-2xl border-0 bg-transparent text-sm "
        "text-stone-700 hover:bg-stone-100"
    )
    class_day_on = (
        "min-h-11 cursor-pointer rounded-2xl border-0 bg-stone-800 text-sm "
        "font-medium text-stone-50"
    )

    month = MorphState("2026-08")
    day = MorphState("2026-08-26")

    def on_pick(self, day: str) -> str:
        """Host seam. Return toast copy after a day is named."""
        return day

    def _month_label(self) -> str:
        y, m = _parse_month(str(self.month or "2026-08"))
        return datetime(y, m, 1).strftime("%B %Y")

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        month = str(self.month or "2026-08")
        y, m = _parse_month(month)
        selected = str(self.day or "")
        weeks = _cal.monthcalendar(y, m)
        header = [
            span(name, className=self.class_dow, role="columnheader")
            for name in _WEEKDAYS
        ]
        rows = [div(*header, className=self.class_row, role="row")]
        for week in weeks:
            cells = []
            for d in week:
                if not d:
                    cells.append(div(span("", className=self.class_empty), role="gridcell"))
                    continue
                key = f"{y:04d}-{m:02d}-{d:02d}"
                on = key == selected
                cells.append(
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
            rows.append(div(*cells, className=self.class_row, role="row"))
        picked = selected or "Nothing chosen"
        return kit_shell(self,
            div(
                button("Prev", type="button", className=self.class_btn_ghost, **bind(self.prev)),
                h2(self._month_label(), className=self.class_title),
                button("Next", type="button", className=self.class_btn_ghost, **bind(self.next)),
                className=self.class_head,
            ),
            div(
                *rows,
                className=self.class_grid,
                role="grid",
                aria_label=self._month_label(),
            ),
            p(picked, className=self.class_lede),
            id=self.id,
            className=self.class_card,
            data_month=f"{y:04d}-{m:02d}",
            data_day=selected,
            chrome=(
                span("Date", className=self.class_kicker),
            ),
        )

    @action(caps=())
    def prev(self):
        self.month = _shift_month(str(self.month or "2026-08"), -1)
        return update_with(self)

    @action(caps=())
    def next(self):
        self.month = _shift_month(str(self.month or "2026-08"), 1)
        return update_with(self)

    @action(caps=())
    def pick(self, day: str = ""):
        if len(day) == 10 and day[4] == "-" and day[7] == "-":
            self.day = day
            self.month = day[:7]
        return update_with(self, extra_ops=[notify(self.on_pick(str(self.day)))])
