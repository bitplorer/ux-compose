"""Drop-in filter bar — labeled query + named filter radiogroup.

Host seam: construct kwargs OR subclass.
Accepted: ``filters``, ``pieces`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``which`` (named filter), ``dirty``. RefState: ``query``.
Caps: none. A11y: region ``role=search``; label ``for`` ↔ query id
``{id}-q``; chips ``role=radiogroup`` / ``radio`` ``aria-checked``;
selected ``tabindex=0`` others ``-1``. Hits are a list. Not SearchBar
(listbox typeahead) — this is chrome that filters a known set in place.
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
    form,
    h2,
    input_,
    label,
    li,
    p,
    span,
    ul,
)


class FilterBar(Kit):
    """Named filter + query. The field keeps focus across morphs (id stable).

    ``FILTERS`` is ``(key, label)``. ``PIECES`` is ``(filter_key, title)``.
    """

    id = "filterbar"
    _SEAMS = {'filters': 'FILTERS', 'pieces': 'PIECES'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_input = (
        "min-h-11 w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 "
        "text-sm outline-none focus:border-stone-400"
    )
    class_chips = "flex flex-wrap gap-1"
    class_chip = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border "
        "border-stone-200 bg-stone-50 px-3 text-xs font-medium"
    )
    class_chip_on = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border-0 "
        "bg-stone-900 px-3 text-xs font-medium text-stone-50"
    )
    class_list = "m-0 flex list-none flex-col gap-1 p-0"
    class_row = "rounded-xl bg-stone-50 px-3 py-2 text-sm"

    FILTERS = (
        ("all", "All"),
        ("linen", "Linen"),
        ("oak", "Oak"),
        ("wool", "Wool"),
    )
    PIECES = (
        ("linen", "Linen work shirt"),
        ("oak", "Oak serving board"),
        ("wool", "Wool throw"),
        ("linen", "Linen napkin"),
    )

    which = MorphState("all")
    query = RefState("")
    dirty = MorphState("idle")

    def _filters(self):
        return tuple(self.FILTERS)

    def _pieces(self):
        return tuple(self.PIECES)

    def _hits(self):
        which = str(self.which or "all")
        q = str(self.query or "").strip().lower()
        rows = []
        for key, title in self._pieces():
            if which not in {"", "all"} and key != which:
                continue
            if q and q not in title.lower() and q not in key:
                continue
            rows.append((key, title))
        return tuple(rows)

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        which = str(self.which or "all")
        keys = {row[0] for row in self._filters()}
        if which not in keys:
            which = self._filters()[0][0]
        q = str(self.query or "")
        fid = f"{self.id}-q"
        title_id = f"{self.id}-label"
        hits = self._hits()
        chips = []
        for k, lab in self._filters():
            on = k == which
            chips.append(
                button(
                    lab,
                    type="button",
                    id=f"{self.id}-opt-{k}",
                    role="radio",
                    aria_checked="true" if on else "false",
                    tabindex="0" if on else "-1",
                    className=self.class_chip_on if on else self.class_chip,
                    **bind(self.choose, key=k),
                )
            )
        rows = [li(title, className=self.class_row) for _k, title in hits]
        body = (
            ul(*rows, className=self.class_list, aria_label="Matches")
            if rows
            else p("No matches.", role="status", className=self.class_lede)
        )
        return self.kit_shell(
            span("Filter", className=self.class_kicker),
            h2("The winter list", id=title_id, className=self.class_title),
            p(
                f"{len(hits)} match" + ("" if len(hits) == 1 else "es") + ".",
                className=self.class_lede,
            ),
            form(
                label("Filter pieces", className=self.class_label, html_for=fid),
                input_(
                    type="search",
                    name="q",
                    id=fid,
                    value=q,
                    placeholder="wool",
                    autocomplete="off",
                    className=self.class_input,
                    **bind(self.set_field, field="q"),
                ),
                div(
                    *chips,
                    className=self.class_chips,
                    role="radiogroup",
                    aria_label="Material",
                ),
                className="flex flex-col gap-2",
                role="search",
            ),
            body,
            id=self.id,
            className=self.class_card,
            data_filter=which,
        )

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("q", ""))
        self.query = "" if raw is None else str(raw)
        self._mark()
        return update_with(self)

    @action(caps=())
    def choose(self, key: str = ""):
        keys = {row[0] for row in self._filters()}
        self.which = key if key in keys else self._filters()[0][0]
        self._mark()
        return update_with(self, extra_ops=[notify(str(self.which))])
