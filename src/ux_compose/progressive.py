"""Progressive levels (0–3) as first-class data."""

from __future__ import annotations

from enum import IntEnum


class Level(IntEnum):
    """Progressive disclosure levels. Higher levels are pure additive unlocks."""
    L0 = 0  # Document + static Components + routing
    L1 = 1  # + Behavior + MorphState + @action (offline interactive)
    L2 = 2  # + Channel + Caps + control stamping (live secure)
    L3 = 3  # + Motion + Scenes + MotionChannel (choreographed)

    @property
    def label(self) -> str:
        return {
            Level.L0: "static SSR",
            Level.L1: "offline interactive",
            Level.L2: "live Caps + morph",
            Level.L3: "choreographed motion",
        }[self]


__all__ = ["Level"]
