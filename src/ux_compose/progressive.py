"""Progressive levels (0–3) as first-class data."""

from __future__ import annotations

from enum import IntEnum


class Level(IntEnum):
    """Progressive disclosure levels. Higher levels are pure additive unlocks.

    L0 — Document + static Components + page-unit routing (ux_compose.routing)
    L1 — + Behavior + MorphState + @action (offline interactive)
    L2 — + Channel + Caps + control()  (HTMX is a separate opt-in control plane)
    L3 — + Motion / Scenes (choreography)

    Progressive Superpower Contract: code written at L1 remains correct
    when you unlock L2/L3 — zero rewrite.
    """

    L0 = 0  # Document + static Components + page-unit routing
    L1 = 1  # + Behavior + MorphState + @action (offline interactive)
    L2 = 2  # + Channel + Caps + control
    L3 = 3  # + Motion / Scenes

    @property
    def label(self) -> str:
        return {
            0: "static + routing",
            1: "offline interactive",
            2: "live channel",
            3: "motion",
        }.get(int(self), str(int(self)))
