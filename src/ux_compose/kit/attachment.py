"""Drop-in attachment — labeled file names on RefState.

Host seam: construct kwargs OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``files``. Caps: none (local list, not
items.delete). A11y: label ``for`` ↔ file id; remove has ``aria-label``.
Not FileUpload (one demo name); this is a stack of chips.
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
    input_,
    label,
    p,
    span,
)


class Attachment(Kit):
    """Pieces on the table. Names live on RefState."""

    id = "attachment"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_chip = "inline-flex min-h-8 items-center gap-1 rounded-full bg-stone-100 px-3 text-xs"
    class_x = "min-h-0 cursor-pointer border-0 bg-transparent p-0 text-stone-500"
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center rounded-full border-0 "
        "bg-stone-800 px-5 text-sm font-medium text-stone-50"
    )
    class_sr = "sr-only"

    files = RefState(("board.pdf",))
    dirty = MorphState("idle")

    def on_add(self, name: str) -> str:
        return name

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        files = tuple(self.files or ())
        fid = f"{self.id}-file"
        chips = [
            span(
                name,
                button("×", type="button", className=self.class_x, aria_label=f"Remove {name}", **bind(self.remove, name=name)),
                className=self.class_chip,
            )
            for name in files
        ]
        return self.kit_shell(
            div(*chips, className="flex flex-wrap gap-2") if chips else p("Nothing attached.", className=self.class_lede),
            label("Attach a file", className=self.class_label, html_for=fid),
            input_(type="text", name="file", id=fid, className=self.class_sr, tabindex="-1"),
            button("Attach sketch.png", type="button", className=self.class_btn, **bind(self.add, name="sketch.png")),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Files", className=self.class_kicker),
                h2("On the board", className=self.class_title),
                p("Names on RefState. Adding is public.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def add(self, name: str = ""):
        name = (name or "sketch.png").strip()
        cur = tuple(self.files or ())
        if name and name not in cur:
            self.files = cur + (name,)
        self._mark()
        return update_with(self, extra_ops=[notify(self.on_add(name))])

    @action(caps=())
    def remove(self, name: str = ""):
        self.files = tuple(x for x in (self.files or ()) if x != name)
        self._mark()
        return update_with(self)
