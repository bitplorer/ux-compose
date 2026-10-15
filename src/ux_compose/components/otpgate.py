"""OtpGate — Identity check. Digits are RefState. Verify is Cap-protected.

Ported from the ``fields`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    App,
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    header,
    ul,
    li,
    span,
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty, status

class OtpGate(Component):
    """Identity check. Digits are RefState. Verify is Cap-protected.

    Typing is public (it only paints). Crossing the gate spends authority.
    """

    id = "otpgate"
    digits = RefState("")
    error = MorphState("")
    ok = MorphState(False)
    dirty = MorphState("idle")
    EXPECT = "2468"

    def render(self):
        d = str(self.digits or "")
        shown = (d + "····")[:4]
        kids = (
            header(
                p("Digits silent · verify is a Cap", className="kicker"),
                h2("OTP gate", className="widget-title"),
            ),
            p("Stand-in code for the studio: 2468. Live Host would SMS it.", className="lede"),
            p(shown, className="num otp-face"),
            form(
                field("code", d, placeholder="4 digits", kind="text"),
                button("Hold digits", type="submit", className="btn-secondary", **control("otpgate.type")),
                method="post",
                action="/act/otpgate.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ),

            div(
                act("otpgate.type", "Fill 2468", kind="ghost", code="2468"),
                act("otpgate.verify", "Verify (Cap)", kind="primary"),
                act("otpgate.reset", "Clear", kind="text"),
                className="row-actions",
            ),
            p(str(self.error), className="error", role="alert") if self.error else p(""),
            status("Gate open.", kind="ok") if self.ok else p(""),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def type(self, code: str = ""):
        self.digits = "".join(ch for ch in str(code or "") if ch.isdigit())[:4]
        self.error = ""
        self.ok = False
        mark_dirty(self)
        return update_with(self)

    @action(caps=())
    def reset(self):
        self.digits = ""
        self.error = ""
        self.ok = False
        mark_dirty(self)
        return update_with(self)

    @action(caps=("auth.verify",))
    def verify(self):
        if str(self.digits or "") != self.EXPECT:
            self.error = "Code does not match"
            self.ok = False
            mark_dirty(self)
            return update_with(self, extra_ops=[notify("mismatch")])
        self.ok = True
        self.error = ""
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("verified")])


__all__ = ["OtpGate"]
