"""Drop-in OTP — six digits attach before the morph.

Host seam: override ``on_verify(code)``. Submit spends ``auth.otp``.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
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


class Otp(Component):
    """One-time code. The typed digits attach onto RefState, then morph.

    Demo: any six digits verify except ``000000``. Override ``on_verify``.
    """

    id = "otp"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-md flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-8 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_label = "text-sm font-medium"
    class_form = "flex flex-col gap-4"
    class_input = (
        "w-full min-h-14 rounded-2xl border border-stone-200 bg-stone-50 "
        "px-4 text-center font-mono text-2xl tracking-[0.4em] text-stone-900 "
        "outline-none focus:border-stone-400 focus:bg-white focus:ring-2 "
        "focus:ring-stone-900/10"
    )
    class_input_err = (
        "w-full min-h-14 rounded-2xl border border-rose-300 bg-stone-50 "
        "px-4 text-center font-mono text-2xl tracking-[0.4em] text-stone-900 "
        "outline-none focus:border-rose-400 focus:bg-white focus:ring-2 "
        "focus:ring-rose-200"
    )
    class_hint = "text-xs text-stone-400"
    class_hint_err = "text-xs text-rose-600"
    class_submit = (
        "min-h-11 w-full cursor-pointer rounded-full border-0 bg-stone-800 "
        "px-5 text-sm font-semibold text-stone-50 hover:bg-stone-700"
    )
    class_ok = "flex flex-col items-center gap-2 py-4 text-center"
    class_mark = (
        "flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 "
        "text-xs font-semibold uppercase tracking-widest text-emerald-700"
    )
    class_btn_ghost = (
        "mt-4 inline-flex min-h-11 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-200 bg-white px-5 text-sm font-medium "
        "text-stone-900 hover:bg-stone-100"
    )

    code = RefState("")
    err = RefState("")
    ok = MorphState(False)
    stamp = MorphState("idle")

    def on_verify(self, code: str) -> str | None:
        """Host seam. Return None to accept, or an error string.

        Demo: ``000000`` is refused. Any other six digits pass.
        """
        if code == "000000":
            return "This code is not valid."
        return None

    def _take(self, code: str = "", **kwargs):
        raw = code if code else kwargs.get("code", "")
        digits = "".join(c for c in str(raw or "") if c.isdigit())[:6]
        self.code = digits

    def _tick(self):
        self.stamp = "b" if self.stamp == "a" else "a"

    def render(self):
        if bool(self.ok):
            return div(
                div(
                    span("Ok", className=self.class_mark),
                    h2("Code accepted", className=self.class_title),
                    p("The Cap was spent. The secret is cleared.", className=self.class_lede),
                    button(
                        "Try another",
                        type="button",
                        className=self.class_btn_ghost,
                        **bind(self.reset),
                    ),
                    className=self.class_ok,
                ),
                id=self.id,
                className=self.class_card,
                data_ok="1",
            )
        code = str(self.code or "")
        err = str(self.err or "")
        return div(
            span("Verify", className=self.class_kicker),
            h2("Enter the code", className=self.class_title),
            p("Six digits. They attach before the morph.", className=self.class_lede),
            form(
                label("One-time code", className=self.class_label),
                input_(
                    type="text",
                    name="code",
                    value=code,
                    maxlength="6",
                    inputmode="numeric",
                    autocomplete="one-time-code",
                    placeholder="••••••",
                    className=self.class_input_err if err else self.class_input,
                    **bind(self.set_field, field="code"),
                ),
                span(err, className=self.class_hint_err, role="alert") if err else span(
                    "Use 123456 in the demo. 000000 is refused.",
                    className=self.class_hint,
                ),
                button(
                    "Verify",
                    type="button",
                    className=self.class_submit,
                    **bind(self.verify),
                ),
                id="otp-form",
                className=self.class_form,
            ),
            id=self.id,
            className=self.class_card,
        )

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("code", ""))
        if field in ("code", ""):
            self._take(code=str(raw or ""))
            self.err = ""
            self._tick()
            return update_with(self)
        return None

    @action(caps=("auth.otp",))
    def verify(self, code: str = "", **kwargs):
        self._take(code=code, **kwargs)
        digits = str(self.code or "")
        if len(digits) != 6:
            self.err = "Enter all six digits."
            self._tick()
            return update_with(self, extra_ops=[notify("Check the code")])
        refused = self.on_verify(digits)
        if refused:
            self.err = refused
            self._tick()
            return update_with(self, extra_ops=[notify(refused)])
        self.ok = True
        self.code = ""
        self.err = ""
        self._tick()
        return update_with(self, extra_ops=[notify("Code accepted")])

    @action(caps=())
    def reset(self):
        self.ok = False
        self.code = ""
        self.err = ""
        self._tick()
        return update_with(self)
