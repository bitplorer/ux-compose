"""Drop-in newsletter — labeled email field, Cap on subscribe.

Host seam: override ``on_join(email)``. Subscribe spends identity/list Cap.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``done``, ``dirty``. RefState: ``email``, ``error``.
Caps: ``list.subscribe``. A11y: label ``for`` ↔ input id; ``aria-invalid``
+ ``aria-describedby`` on errors.
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
    form,
    h2,
    input_,
    label,
    p,
    span,
)


class Newsletter(Component):
    """Join the winter list. Email is RefState. Subscribe is a Cap."""

    id = "newsletter"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_input = (
        "w-full min-h-11 rounded-2xl border border-stone-200 bg-stone-50 px-4 text-sm outline-none"
    )
    class_input_err = (
        "w-full min-h-11 rounded-2xl border border-rose-300 bg-stone-50 px-4 text-sm outline-none"
    )
    class_hint_err = "text-xs text-rose-600"
    class_btn = (
        "min-h-11 w-full cursor-pointer rounded-full border-0 bg-stone-800 px-5 "
        "text-sm font-semibold text-stone-50 hover:bg-stone-700"
    )

    email = RefState("")
    error = RefState("")
    done = MorphState(False)
    dirty = MorphState("idle")

    def on_join(self, email: str) -> str:
        return f"Joined as {email}"

    def render(self):
        if bool(self.done):
            return div(
                span("In", className=self.class_kicker),
                h2("You're on the list", className=self.class_title),
                p("A letter when the linen lands.", className=self.class_lede),
                id=self.id,
                className=self.class_card,
                data_done="1",
            )
        fid = f"{self.id}-email"
        err = str(self.error or "")
        err_id = f"{fid}-err"
        return div(
            span("Letter", className=self.class_kicker),
            h2("Winter list", className=self.class_title),
            p("No spam, ever.", className=self.class_lede),
            form(
                label("Email", className=self.class_label, html_for=fid),
                input_(
                    type="email",
                    name="email",
                    id=fid,
                    value=str(self.email or ""),
                    placeholder="you@atelier.test",
                    autocomplete="email",
                    className=self.class_input_err if err else self.class_input,
                    aria_invalid="true" if err else "false",
                    **({"aria_describedby": err_id} if err else {}),
                    **bind(self.set_field, field="email"),
                ),
                span(err, id=err_id, className=self.class_hint_err, role="alert") if err else span("", className="sr-only"),
                button("Join", type="button", className=self.class_btn, **bind(self.subscribe)),
                className="flex flex-col gap-2",
            ),
            id=self.id,
            className=self.class_card,
            data_done="0",
        )

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("email", ""))
        self.email = "" if raw is None else str(raw)
        self.error = ""
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self)

    @action(caps=("list.subscribe",))
    def subscribe(self, email: str = ""):
        if email:
            self.email = email
        addr = str(self.email or "").strip()
        if "@" not in addr or "." not in addr.split("@")[-1]:
            self.error = "Enter a valid email address."
            self.dirty = "b" if self.dirty == "a" else "a"
            return update_with(self, extra_ops=[notify("Check the email")])
        self.done = True
        return update_with(self, extra_ops=[notify(self.on_join(addr))])
