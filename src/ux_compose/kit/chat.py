"""Drop-in chat — live log, labeled composer, public send.

Host seam: render slots OR subclass.
Accepted: (none — ``shell`` only); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``typing``, ``dirty``. RefState: ``lines``, ``draft``.
Caps: none (not spend / delete / identity). A11y: transcript ``role=log``
``aria-live=polite``; label ``for`` ↔ composer id ``{id}-draft``.
Typing is qualitative MorphState. Lines are a list on RefState.
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


class Chat(Component):
    """A short desk thread. The log is RefState; typing is MorphState."""

    id = "chat"
    _SEAMS = {}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_log = "m-0 flex max-h-56 list-none flex-col gap-1 overflow-y-auto p-0"
    class_line = "rounded-xl bg-stone-50 px-3 py-2 text-sm"
    class_label = "text-sm font-medium"
    class_input = (
        "min-h-11 w-full rounded-2xl border border-stone-200 bg-stone-50 px-4 "
        "text-sm outline-none focus:border-stone-400"
    )
    class_btn = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50"
    )

    lines = RefState(("Atelier: the table is set.",))
    draft = RefState("")
    typing = MorphState(False)
    dirty = MorphState("idle")

    def on_send(self, text: str) -> str:
        return "sent"

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        lines = tuple(self.lines or ())
        draft = str(self.draft or "")
        typing = bool(self.typing)
        fid = f"{self.id}-draft"
        log_id = f"{self.id}-log"
        rows = [li(x, className=self.class_line) for x in lines]
        status = (
            p("Atelier is typing…", className=self.class_lede, role="status")
            if typing
            else p(f"{len(lines)} line" + ("" if len(lines) == 1 else "s") + ".", className=self.class_lede)
        )
        return kit_shell(self,
            status,
            ul(
                *rows,
                id=log_id,
                className=self.class_log,
                role="log",
                aria_live="polite",
                aria_relevant="additions",
                aria_label="Thread",
            ),
            form(
                label("Write a line", className=self.class_label, html_for=fid),
                input_(
                    type="text",
                    name="text",
                    id=fid,
                    value=draft,
                    placeholder="Write a line",
                    autocomplete="off",
                    className=self.class_input,
                    **bind(self.set_field, field="text"),
                ),
                button("Send", type="button", className=self.class_btn, **bind(self.send)),
                className="flex flex-col gap-2",
            ),
            id=self.id,
            className=self.class_card,
            data_typing="1" if typing else "0",
            chrome=(
                span("Desk", className=self.class_kicker),
                h2("Chat", className=self.class_title),
            ),
        )

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("text", ""))
        self.draft = "" if raw is None else str(raw)
        self._mark()
        return update_with(self)

    @action(caps=())
    def send(self, text: str = ""):
        line = (text or str(self.draft or "")).strip() or "…"
        self.lines = tuple(self.lines or ()) + (f"You: {line}",)
        self.draft = ""
        self.typing = False
        self._mark()
        return update_with(self, extra_ops=[notify(self.on_send(line))])

    @action(caps=())
    def peer_type(self):
        self.typing = True
        return update_with(self)

    @action(caps=())
    def peer_done(self):
        self.typing = False
        self.lines = tuple(self.lines or ()) + ("Atelier: held until you place.",)
        self._mark()
        return update_with(self)
