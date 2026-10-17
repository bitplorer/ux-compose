"""LiveOrder — LiveOrder

Ported from the ``live_caps`` example module (spec §4); this module is canonical and the example imports it.
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
    span,
)

from ux_compose.author import act, mark_dirty

class LiveOrder(Component):
    id = "liveorder"
    status = MorphState("idle")  # idle | ready | placed | refused
    note = RefState("No Cap presented.")

    def render(self):
        st = str(self.status or "idle")
        kids = (
            header(
                p("Authority Clock", className="kicker"),
                h2("Live Cap checkout", className="widget-title"),
            ),
            p(span(st, className="chip"), className="chip-row"),
            p(str(self.note or ""), className="lede"),
            p(
                "Place is Cap-protected. The host must mint. A bare click is not enough.",
                className="muted",
            ),
            div(
                act("liveorder.prepare", "Prepare order", kind="secondary"),
                act("liveorder.place", "Place without Cap", kind="ghost"),
                act("liveorder.place_minted", "Host mints Cap + place", kind="primary"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget", data_status=st)

    @action(caps=())
    def prepare(self):
        self.status = "ready"
        self.note = "Ready. Placing still needs a Cap."
        return update_with(self)

    @action(caps=("orders.place",))
    def place(self):
        self.status = "placed"
        self.note = "Cap accepted. Order is on the table."
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("placed")])

    @action(caps=("orders.place",))
    def place_minted(self):
        """Studio host intercepts this name and calls submit_intent(mint=True).

        Same Cap as ``place``: offline it fails closed like ``place`` does.
        """
        self.status = "placed"
        self.note = "Host-mint path (studio): Cap minted for orders.place."
        return update_with(self, extra_ops=[notify("minted-path")])

    @action(caps=())
    def mark_refused(self, reason: str = "no Cap"):
        self.status = "refused"
        self.note = f"Refused — {reason}."
        return update_with(self, extra_ops=[notify("refused")])


__all__ = ["LiveOrder"]
