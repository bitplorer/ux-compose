"""Coupon — Code is a string MorphState (qualitative). Discount amount is RefState.

Ported from the ``commerce_more`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
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
    form,
    button,
    control,
)

from ux_compose.author import act, field, mark_dirty, status

CATALOG = {
    "linen": ("Work shirt", 48),
    "oak": ("Serving board", 72),
    "wool": ("Throw", 96),
    "clay": ("Pourer", 38),
}

class Coupon(Component):
    """Code is a string MorphState (qualitative). Discount amount is RefState.

    Checking a code is public. Redeeming it (changing the payable) is a Cap.
    """

    id = "coupon"
    code = MorphState("")
    applied = MorphState(False)
    off = RefState(0)
    error = MorphState("")
    dirty = MorphState("idle")
    VALID = {"HOUSE10": 10, "LINEN": 8}

    def render(self):
        kids = (
            header(
                p("Code is a name · redeem is a Cap", className="kicker"),
                h2("Coupon", className="widget-title"),
            ),
            p("Try HOUSE10 or LINEN. Checking is public. Redeeming spends authority.", className="lede"),
            form(
                field("code", str(self.code or ""), placeholder="Code"),
                button("Check", type="submit", className="btn-secondary", **control("coupon.check")),
                method="post",
                action="/act/coupon.check",
                data_ux="1",
                data_target="#stage",
                className="stack",
            ),

            div(
                act("coupon.check", "Check HOUSE10", kind="ghost", code="HOUSE10"),
                act("coupon.redeem", "Redeem (Cap)", kind="primary"),
                act("coupon.clear", "Clear", kind="text"),
                className="row-actions",
            ),
            p(str(self.error), className="error", role="alert") if self.error else p(""),
            status(f"Held · {self.off} off." if self.applied else "", kind="ok"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def check(self, code: str = ""):
        code = (code or str(self.code or "")).strip().upper()
        self.code = code
        self.applied = False
        self.off = 0
        if code in self.VALID:
            self.error = ""
        else:
            self.error = "Unknown code"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("checked")])

    @action(caps=())
    def clear(self):
        self.code = ""
        self.applied = False
        self.off = 0
        self.error = ""
        mark_dirty(self)
        return update_with(self)

    @action(caps=("coupons.redeem",))
    def redeem(self):
        code = str(self.code or "").upper()
        if code not in self.VALID:
            self.error = "Check a valid code first"
            mark_dirty(self)
            return update_with(self, extra_ops=[notify("blocked")])
        self.applied = True
        self.off = self.VALID[code]
        self.error = ""
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(f"off {self.off}")])


__all__ = ["Coupon"]
