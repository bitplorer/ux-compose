"""Drop-in search bar — labeled query field, hits as a list.

Host seam: render slots OR subclass.
Accepted: ``options`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``query``. Caps: none. A11y: label ``for``
↔ input id; results ``role=listbox``.
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
    form,
    h2,
    input_,
    label,
    li,
    p,
    span,
    ul,
)


class SearchBar(Component):
    """Filter in place. The field keeps focus across morphs (id stable)."""

    id = "searchbar"
    _SEAMS = {'options': 'OPTIONS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_form = "flex gap-2"
    class_input = (
        "min-h-11 w-full flex-1 rounded-2xl border border-stone-200 bg-stone-50 px-4 "
        "text-sm outline-none focus:border-stone-400"
    )
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50"
    )
    class_list = "m-0 flex list-none flex-col gap-1 p-0"
    class_row = "rounded-xl bg-stone-50 px-3 py-2 text-sm"

    OPTIONS = ("Linen work shirt", "Oak serving board", "Wool throw", "Clay pourer")

    query = RefState("")
    dirty = MorphState("idle")

    def _hits(self):
        q = str(self.query or "").strip().lower()
        opts = tuple(self.OPTIONS)
        if not q:
            return opts
        return tuple(x for x in opts if q in x.lower())

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        q = str(self.query or "")
        fid = f"{self.id}-q"
        hits = self._hits()
        rows = [li(x, className=self.class_row, role="option") for x in hits]
        return kit_shell(self,
            p(f"{len(hits)} match" + ("" if len(hits) == 1 else "es") + ".", className=self.class_lede),
            form(
                label("Search the catalog", className=self.class_label, html_for=fid),
                input_(
                    type="search",
                    name="q",
                    id=fid,
                    value=q,
                    placeholder="Filter pieces",
                    autocomplete="off",
                    className=self.class_input,
                    **bind(self.set_field, field="q"),
                ),
                button("Search", type="button", className=self.class_btn, **bind(self.search)),
                className=self.class_form + " flex-col",
            ),
            ul(*rows, className=self.class_list, role="listbox", aria_label="Results") if rows else p("No matches.", role="status", className=self.class_lede),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Find", className=self.class_kicker),
                h2("Search", className=self.class_title),
            ),
        )

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("q", ""))
        self.query = "" if raw is None else str(raw)
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self)

    @action(caps=())
    def search(self, q: str = ""):
        if q:
            self.query = q
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self, extra_ops=[notify(str(self.query or "all"))])
