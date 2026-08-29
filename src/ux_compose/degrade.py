"""Visible progressive degrade — silence was the defect, not degrade itself.

Level 1 code must keep working when Channel / Motion / CEK are absent.
That contract is frozen. What this module adds is an evidence list so
``doctor`` and tests can see *why* a higher level did not attach.

Public surface is additive. Nothing in the 0.1.0 path is required to call
``note()``. Wire / App may start recording without changing return values.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class DegradeEvent:
    """One specialist attach that stepped down instead of raising."""

    door: str
    wanted: str
    reason: str
    level_kept: int = 1


_EVENTS: List[DegradeEvent] = []


def note(
    door: str,
    wanted: str,
    reason: str,
    *,
    level_kept: int = 1,
) -> DegradeEvent:
    """Record a degrade. Never raises. Safe to call from except blocks."""
    event = DegradeEvent(
        door=door,
        wanted=wanted,
        reason=str(reason),
        level_kept=level_kept,
    )
    _EVENTS.append(event)
    return event


def degrades() -> tuple[DegradeEvent, ...]:
    """Snapshot of degrade events for this process."""
    return tuple(_EVENTS)


def clear() -> None:
    """Test helper — do not call from product code."""
    _EVENTS.clear()


def format_report(events: Optional[List[DegradeEvent]] = None) -> list[str]:
    rows = events if events is not None else list(_EVENTS)
    return [
        f"degrade {e.door}: wanted {e.wanted}, kept L{e.level_kept} ({e.reason})"
        for e in rows
    ]


__all__ = ["DegradeEvent", "note", "degrades", "clear", "format_report"]
