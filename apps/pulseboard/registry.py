"""Live unit lookup — filled after build() / atelier UX.add."""

from __future__ import annotations

from typing import Any

UNITS: dict[str, Any] = {}


def bind(registry: dict[str, Any] | None) -> None:
    UNITS.clear()
    if registry:
        UNITS.update(registry)


def live(sid: str) -> Any | None:
    return UNITS.get(sid)


def theme_key() -> str:
    inst = live("desk_theme")
    if inst is None:
        return "dark"
    key = str(getattr(inst, "value", "dark") or "dark")
    if key == "system":
        return "dark"
    return key if key in {"light", "dark"} else "dark"
