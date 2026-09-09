"""Drop-in tags input — named chips, RefState list, labeled field.

Host seam: construct kwargs OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``tags``, ``draft``. Caps: none.
A11y: label ``for`` ↔ input id; chips are buttons with ``aria-label`` remove.
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
    p,
    span,
)


class TagsInput(Kit):
    """A set of names. Quantity of chips lives on RefState."""

    id = "tagsinput"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_row = "flex flex-wrap gap-2"
    class_chip = (
        "inline-flex min-h-8 items-center gap-1 rounded-full bg-stone-100 px-3 text-xs font-medium"
    )
    class_x = "min-h-0 cursor-pointer border-0 bg-transparent p-0 text-stone-500"
    class_input = (
        "min-h-11 w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 text-sm outline-none"
    )
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50"
    )

    tags = RefState(("linen", "oak"))
    draft = RefState("")
    dirty = MorphState("idle")

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        tags = tuple(self.tags or ())
        draft = str(self.draft or "")
        fid = f"{self.id}-draft"
        chips = [
            span(
                t,
                button("×", type="button", className=self.class_x, aria_label=f"Remove {t}", **bind(self.remove, tag=t)),
                className=self.class_chip,
            )
            for t in tags
        ]
        return self.kit_shell(
            div(*chips, className=self.class_row) if chips else p("No tags yet.", className=self.class_lede),
            form(
                label("Add a tag", className=self.class_label, html_for=fid),
                input_(
                    type="text",
                    name="tag",
                    id=fid,
                    value=draft,
                    placeholder="wool",
                    className=self.class_input,
                    **bind(self.set_field, field="tag"),
                ),
                button("Add", type="button", className=self.class_btn, **bind(self.add)),
                className="flex flex-col gap-2",
            ),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Tags", className=self.class_kicker),
                h2("Name the piece", className=self.class_title),
                p("Chips are names. The field is labeled.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("tag", ""))
        self.draft = "" if raw is None else str(raw)
        self._mark()
        return update_with(self)

    @action(caps=())
    def add(self, tag: str = ""):
        name = (tag or str(self.draft or "")).strip().lower()
        cur = tuple(self.tags or ())
        if name and name not in cur:
            self.tags = cur + (name,)
        self.draft = ""
        self._mark()
        return update_with(self, extra_ops=[notify(name or "empty")])

    @action(caps=())
    def remove(self, tag: str = ""):
        self.tags = tuple(t for t in (self.tags or ()) if t != tag)
        self._mark()
        return update_with(self)
