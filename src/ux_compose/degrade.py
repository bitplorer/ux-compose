"""Visible progressive degrade — silence was the defect, not degrade itself.

Level 1 code must keep working when Channel / Motion / CEK are absent.
That contract is frozen. Evidence is per-App. A process bus is the
fallback when no App is bound (doctor, tests, import-time).

Public surface is additive. Attach methods still do not raise.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator, List, Optional


@dataclass(frozen=True)
class DegradeEvent:
    """One specialist attach that stepped down instead of raising."""

    door: str
    wanted: str
    reason: str
    level_kept: int = 1


class DegradeBus:
    """One App's attach evidence."""

    def __init__(self) -> None:
        self._events: list[DegradeEvent] = []

    def note(
        self,
        door: str,
        wanted: str,
        reason: str,
        *,
        level_kept: int = 1,
    ) -> DegradeEvent:
        event = DegradeEvent(
            door=door,
            wanted=wanted,
            reason=str(reason),
            level_kept=level_kept,
        )
        self._append(event)
        return event

    def snapshot(self) -> tuple[DegradeEvent, ...]:
        return tuple(self._events)

    def clear(self) -> None:
        self._events.clear()

    def _append(self, event: DegradeEvent) -> None:
        self._events.append(event)


_PROCESS = DegradeBus()
_ACTIVE: ContextVar[DegradeBus] = ContextVar("ux_compose_degrade", default=_PROCESS)


def current() -> DegradeBus:
    return _ACTIVE.get()


@contextmanager
def using(bus: DegradeBus) -> Iterator[DegradeBus]:
    """Bind this bus as the active evidence list for the block."""
    token: Token = _ACTIVE.set(bus)
    try:
        yield bus
    finally:
        _ACTIVE.reset(token)


def note(
    door: str,
    wanted: str,
    reason: str,
    *,
    level_kept: int = 1,
) -> DegradeEvent:
    """Record a degrade. Never raises. Safe to call from except blocks.

    Writes the active bus. Dual-writes the process bus so doctor always
    has a process-wide audit even when an App is bound.
    """
    bus = current()
    event = bus.note(door, wanted, reason, level_kept=level_kept)
    if bus is not _PROCESS:
        _PROCESS._append(event)
    return event


def degrades() -> tuple[DegradeEvent, ...]:
    """Snapshot of the active bus (process bus when no App is bound)."""
    return current().snapshot()


def clear() -> None:
    """Test helper — do not call from product code."""
    bus = current()
    bus.clear()
    if bus is not _PROCESS:
        _PROCESS.clear()


def format_report(events: Optional[List[DegradeEvent]] = None) -> list[str]:
    rows = events if events is not None else list(_PROCESS.snapshot())
    return [
        f"degrade {e.door}: wanted {e.wanted}, kept L{e.level_kept} ({e.reason})"
        for e in rows
    ]


__all__ = [
    "DegradeEvent",
    "DegradeBus",
    "note",
    "degrades",
    "clear",
    "format_report",
    "using",
    "current",
]
