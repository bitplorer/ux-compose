"""Live Caps — Authority Clock.

Cap Law:
  - ``@action(caps=())`` is open mint / no Cap predicate.
    Offline dispatch always allowed. Intent still requires the
    control-minted cap under Cap Host require.
  - ``@action(caps=("orders.place",))`` is protected.
      Offline + strict_caps=True  → AuthorityError (fail closed)
      Live                       → Intent must carry a Channel-minted Cap

Product code never imports ux_channel. Host mints through ``App.mint_cap`` /
``App.submit_intent`` (wire/ door). After ``use_channel``, ``App.dispatch``
is Host-internal (specialist contract) — live verification is submit_intent.

Offline Cap Law runs at L1. After use_channel, live mint/refuse is fail-loud.

Run:
  PYTHONPATH=src:. python examples/live_caps.py
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
    doctor,
    div,
    h2,
    p,
    header,
    span,
)

from examples._common import act, mark_dirty


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

    @action(caps=())
    def place_minted(self):
        """Studio host intercepts this name and calls submit_intent(mint=True).

        Offline this is an open-mint stand-in so the file still runs at L1.
        """
        self.status = "placed"
        self.note = "Host-mint path (studio). Offline this is an open-mint stand-in."
        return update_with(self, extra_ops=[notify("minted-path")])

    @action(caps=())
    def mark_refused(self, reason: str = "no Cap"):
        self.status = "refused"
        self.note = f"Refused — {reason}."
        return update_with(self, extra_ops=[notify("refused")])


def demo() -> None:
    app = App.boot("Caps", strict_caps=False)
    app.add(LiveOrder)
    print("prepare", app.dispatch("liveorder.prepare"))
    print("open-mint path", app.dispatch("liveorder.place_minted"))

    strict = App.boot("Caps", strict_caps=True)
    strict.add(LiveOrder)
    try:
        strict.dispatch("liveorder.place")
        print("UNEXPECTED place")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__, "— place refused offline under strict_caps")

    # Live mint path — Channel is a hard dep after use_channel
    live = App.boot("Caps", strict_caps=True)
    live.add(LiveOrder)
    live.use_channel()
    if live._channel is None:
        raise RuntimeError(
            "Channel missing after use_channel — ux-channel is a hard dependency"
        )
    refused = live.submit_intent("liveorder.place", mint=False)
    print("no cap ok?", getattr(refused, "ok", None))
    # Default mint is once=False (reusable). Checkout spends once.
    cap = live.mint_cap("liveorder.place", {}, once=True)
    placed = live.submit_intent("liveorder.place", cap=cap)
    print("minted once ok?", getattr(placed, "ok", None))
    replay = live.submit_intent("liveorder.place", cap=cap)
    print("replay ok?", getattr(replay, "ok", None))

    report = doctor([], fail=False)
    print("Doctor", report.ok, report.capabilities)


if __name__ == "__main__":
    demo()
