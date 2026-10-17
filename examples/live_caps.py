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
    doctor,
)

from ux_compose.components.liveorder import LiveOrder


def demo() -> None:
    app = App.boot("Caps")
    app.add(LiveOrder)
    print("prepare", app.dispatch("liveorder.prepare"))
    try:
        app.dispatch("liveorder.place_minted")
        print("UNEXPECTED place_minted")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__, "— place_minted needs the same Cap as place")

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
