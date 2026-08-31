"""Visible attach step-down — silence was the defect, not the step-down.

Level 1 code must keep working when Channel / Motion / CEK are absent.
That contract is frozen. Evidence is per-App.

Public author names: AttachNote, attach_notes().
AttachNotes is the notebook one App owns. It is not a message bus.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Iterator, List, Optional


@dataclass(frozen=True)
class AttachNote:
    """One specialist attach that stepped down instead of raising."""

    door: str
    wanted: str
    reason: str
    level_kept: int = 1


class AttachNotes:
    """One App's attach notes."""

    def __init__(self) -> None:
        self._notes: list[AttachNote] = []

    def add(
        self,
        door: str,
        wanted: str,
        reason: str,
        *,
        level_kept: int = 1,
    ) -> AttachNote:
        item = AttachNote(
            door=door,
            wanted=wanted,
            reason=str(reason),
            level_kept=level_kept,
        )
        self._notes.append(item)
        return item

    def snapshot(self) -> tuple[AttachNote, ...]:
        return tuple(self._notes)

    def clear(self) -> None:
        self._notes.clear()

    def _append(self, item: AttachNote) -> None:
        self._notes.append(item)


_PROCESS = AttachNotes()
_ACTIVE: ContextVar[AttachNotes] = ContextVar("ux_compose_attach_notes", default=_PROCESS)


def current() -> AttachNotes:
    return _ACTIVE.get()


@contextmanager
def using(notes: AttachNotes) -> Iterator[AttachNotes]:
    """Bind this notebook as the active list for the block."""
    token: Token = _ACTIVE.set(notes)
    try:
        yield notes
    finally:
        _ACTIVE.reset(token)


def note(
    door: str,
    wanted: str,
    reason: str,
    *,
    level_kept: int = 1,
) -> AttachNote:
    """Record a step-down. Never raises. Safe to call from except blocks."""
    notes = current()
    item = notes.add(door, wanted, reason, level_kept=level_kept)
    if notes is not _PROCESS:
        _PROCESS._append(item)
    return item


def attach_notes() -> tuple[AttachNote, ...]:
    """Snapshot of the active notebook (process-wide when no App is bound)."""
    return current().snapshot()


def clear() -> None:
    """Test helper — do not call from product code."""
    notes = current()
    notes.clear()
    if notes is not _PROCESS:
        _PROCESS.clear()


def format_report(items: Optional[List[AttachNote]] = None) -> list[str]:
    rows = items if items is not None else list(_PROCESS.snapshot())
    return [
        f"attach {e.door}: wanted {e.wanted}, kept L{e.level_kept} ({e.reason})"
        for e in rows
    ]


__all__ = [
    "AttachNote",
    "AttachNotes",
    "note",
    "attach_notes",
    "clear",
    "format_report",
    "using",
    "current",
]
