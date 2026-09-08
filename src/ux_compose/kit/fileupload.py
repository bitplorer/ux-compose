"""Drop-in file upload — labeled file control + named list.

Host seam: override ``on_add(name)``. Adding is public in the demo.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``files``. Caps: none (Host may add a Cap).
A11y: label ``for`` ↔ file input id; list of names.
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
    input_,
    label,
    li,
    p,
    span,
    ul,
)


class FileUpload(Component):
    """Named files on RefState. The input is labeled. Magnitude is the list."""

    id = "fileupload"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_input = "w-full min-h-11 text-sm file:mr-3 file:rounded-full file:border-0 file:bg-stone-800 file:px-4 file:py-2 file:text-sm file:text-stone-50"
    class_list = "m-0 flex list-none flex-col gap-1 p-0"
    class_row = "flex min-h-11 items-center justify-between rounded-xl bg-stone-50 px-3 text-sm"
    class_x = "min-h-11 cursor-pointer rounded-full border-0 bg-transparent px-3 text-sm"

    files = RefState(("moodboard.pdf",))
    dirty = MorphState("idle")

    def on_add(self, name: str) -> str:
        return name

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        fid = f"{self.id}-file"
        names = tuple(self.files or ())
        rows = [
            li(
                span(name),
                button("Remove", type="button", className=self.class_x, **bind(self.remove, name=name)),
                className=self.class_row,
            )
            for name in names
        ]
        return div(
            span("Files", className=self.class_kicker),
            h2("Attach a note", className=self.class_title),
            p(f"{len(names)} file" + ("" if len(names) == 1 else "s") + " on the table.", className=self.class_lede),
            label("Choose a file", className=self.class_label, html_for=fid),
            input_(type="file", name="file", id=fid, className=self.class_input, **bind(self.add, name="sketch.png")),
            ul(*rows, className=self.class_list) if rows else p("Nothing attached.", className=self.class_lede),
            id=self.id,
            className=self.class_card,
        )

    @action(caps=())
    def add(self, name: str = "sketch.png"):
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
