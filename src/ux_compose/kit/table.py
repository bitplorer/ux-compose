"""Drop-in data table — sort key MorphState, selection RefState.

Host seam: construct kwargs OR subclass.
Accepted: ``columns``, ``rows`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Archiving spends a Cap. Selecting is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``sort``, ``cleared``, ``dirty``. RefState: ``items``, ``selected``.
Caps: ``items.archive`` on ``archive``. ``toggle_row`` / ``toggle_all`` / ``sort_by`` are public.
A11y (APG Table): native ``<table>``, ``scope=col`` on ``th``. Row activation
calls ``toggle_row`` (one sku). Header checkbox is ``toggle_all`` — it is not
a body click and does not share the row bind. Row checkbox is a focusable
``role=checkbox`` (keyboard/AT, not decorative spans). Bind lives on that
checkbox, not the ``<tr>``. ``aria-selected`` on the row.
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
    p,
    span,
    table,
    tbody,
    td,
    th,
    thead,
    tr,
)


class Table(Kit):
    """Sortable rows with a selection set.

    ``COLUMNS`` is ``(key, label)``. ``ROWS`` is ``(sku, {col: value})``.
    Quantity never lives on MorphState.
    """

    id = "table"
    _SEAMS = {'columns': 'COLUMNS', 'rows': 'ROWS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-[44rem] flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_danger = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-rose-800 px-5 text-sm font-medium text-rose-50 hover:bg-rose-700"
    )
    class_btn_muted = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-400"
    )
    class_toolbar = "flex flex-wrap items-center justify-between gap-3"
    class_wrap = "overflow-x-auto"
    class_table = "w-full min-w-[28rem] border-separate border-spacing-y-0.5 text-left"
    class_th = (
        "min-h-11 cursor-pointer border-0 bg-transparent p-0 text-left text-xs "
        "font-semibold uppercase tracking-widest text-stone-400"
    )
    class_th_on = (
        "min-h-11 cursor-pointer border-0 bg-transparent p-0 text-left text-xs "
        "font-semibold uppercase tracking-widest text-stone-900"
    )
    class_tr = "rounded-xl hover:bg-stone-50"
    class_tr_on = "rounded-xl bg-stone-100"
    class_td = "px-1.5 py-2 text-sm"
    class_td_price = "px-1.5 py-2 text-sm tabular-nums"
    class_check = (
        "flex h-11 w-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent p-0"
    )
    class_box = (
        "flex h-5 w-5 items-center justify-center rounded-md border border-stone-300 "
        "bg-white text-[0.65rem] font-semibold text-white"
    )
    class_box_on = (
        "flex h-5 w-5 items-center justify-center rounded-md border-0 "
        "bg-stone-800 text-[0.65rem] font-semibold text-white"
    )
    class_sr = "sr-only"

    COLUMNS = (
        ("name", "Piece"),
        ("stage", "Stage"),
        ("price", "Price"),
    )
    ROWS = (
        ("linen-01", {"name": "Work shirt", "stage": "cut", "price": "48"}),
        ("oak-02", {"name": "Serving board", "stage": "make", "price": "72"}),
        ("wool-03", {"name": "Throw", "stage": "keep", "price": "96"}),
        ("clay-04", {"name": "Pourer", "stage": "cut", "price": "38"}),
    )

    items = RefState(())
    cleared = MorphState(False)
    sort = MorphState("name")
    selected = RefState(())
    dirty = MorphState("idle")

    def on_archive(self, skus: tuple[str, ...]) -> str:
        """Host seam. Return toast copy after the Cap spent."""
        n = len(skus)
        return f"Archived {n} piece" if n == 1 else f"Archived {n} pieces"

    def _mark_dirty(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def _rows(self):
        key = str(self.sort or "name")
        if bool(self.cleared):
            rows = list(self.items or ())
        else:
            live = tuple(self.items or ())
            rows = list(live if live else self.ROWS)

        def val(row):
            return str((row[1] or {}).get(key, ""))

        return tuple(sorted(rows, key=val))

    def _cell(self, key: str, cols: dict) -> str:
        raw = str(cols.get(key, ""))
        if key == "price" and raw and not raw.startswith("$"):
            return f"${raw}"
        return raw

    def render(self):
        sel = set(self.selected or ())
        sort = str(self.sort or "name")
        known = [row[0] for row in self._rows()]
        all_on = bool(known) and set(known) <= sel
        heads = [
            th(
                button(
                    span("On" if all_on else "Off", className=self.class_sr),
                    span("✓" if all_on else "", className=self.class_box_on if all_on else self.class_box),
                    type="button",
                    className=self.class_check,
                    role="checkbox",
                    aria_checked="true" if all_on else "false",
                    aria_label="Select all rows",
                    **bind(self.toggle_all),
                ),
                scope="col",
                className="w-11 px-1.5",
            )
        ]
        for key, label in self.COLUMNS:
            on = key == sort
            heads.append(
                th(
                    button(
                        f"{label} ▾" if on else label,
                        type="button",
                        className=self.class_th_on if on else self.class_th,
                        **bind(self.sort_by, key=key),
                    ),
                    scope="col",
                )
            )
        body = []
        for sku, cols in self._rows():
            on = sku in sel
            cells = [
                td(
                    self._cell(k, cols),
                    className=self.class_td_price if k == "price" else self.class_td,
                )
                for k, _ in self.COLUMNS
            ]
            name = self._cell("name", cols)
            body.append(
                tr(
                    td(
                        button(
                            span("On" if on else "Off", className=self.class_sr),
                            span("✓" if on else "", className=self.class_box_on if on else self.class_box),
                            type="button",
                            className=self.class_check,
                            role="checkbox",
                            aria_checked="true" if on else "false",
                            aria_label=f"Select {name}",
                            **bind(self.toggle_row, sku=sku),
                        ),
                        className="px-1.5",
                    ),
                    *cells,
                    id=f"row-{sku}",
                    className=self.class_tr_on if on else self.class_tr,
                    aria_selected="true" if on else "false",
                )
            )
        empty = not body
        n = len(sel)
        return self.kit_shell(
            div(
                p(f"{n} selected", className=self.class_lede),
                button(
                    "Archive selected",
                    type="button",
                    className=self.class_btn_danger if n else self.class_btn_muted,
                    **bind(self.archive),
                ),
                className=self.class_toolbar,
            ),
            div(
                table(
                    thead(tr(*heads)),
                    tbody(*body) if body else tbody(
                        tr(td("Nothing on the table.", className=self.class_lede, colspan=str(1 + len(self.COLUMNS))))
                    ),
                    className=self.class_table,
                ),
                className=self.class_wrap,
            ),
            p("", className=self.class_sr) if empty else span("", className=self.class_sr),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Catalog", className=self.class_kicker),
                h2("Pieces on the table", className=self.class_title),
            ),
        )

    @action(caps=())
    def sort_by(self, key: str = "name"):
        keys = {k for k, _ in self.COLUMNS}
        self.sort = key if key in keys else "name"
        return update_with(self)

    @action(caps=())
    def toggle_row(self, sku: str = ""):
        known = {row[0] for row in self._rows()}
        cur = set(self.selected or ())
        if sku in cur:
            cur.remove(sku)
        elif sku and sku in known:
            cur.add(sku)
        self.selected = tuple(sorted(cur))
        self._mark_dirty()
        return update_with(self)

    @action(caps=())
    def toggle_all(self):
        """Header checkbox. Never shares ``toggle_row`` — body click is one sku."""
        known = {row[0] for row in self._rows()}
        cur = set(self.selected or ())
        self.selected = () if known and known <= cur else tuple(sorted(known))
        self._mark_dirty()
        return update_with(self)

    @action(caps=("items.archive",))
    def archive(self):
        skus = tuple(self.selected or ())
        if not skus:
            return update_with(self, extra_ops=[notify("Nothing selected")])
        remaining = tuple(row for row in self._rows() if row[0] not in set(skus))
        self.items = remaining
        self.cleared = True
        self.selected = ()
        self._mark_dirty()
        return update_with(self, extra_ops=[notify(self.on_archive(skus))])
