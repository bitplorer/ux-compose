"""Render a visible stand-in when a component is used without its required data.

Modes (spec §3):
- ``show``  — dashed box naming the component and the missing params (dev, Atelier, tests)
- ``hide``  — default; hidden root that keeps the morph id, no names; logs once per
  (class, missing set) on the ``ux_compose.placeholder`` logger and emits a warning
- ``raise`` — ``MissingParams`` (a ``TypeError``) naming the component and params

Pick a mode with ``use_placeholder_mode(...)`` or the ``UX_COMPOSE_PLACEHOLDERS``
environment variable (an unknown value raises ``ValueError``). ``uxcompose serve dev``
sets ``show`` on the worker processes it spawns only.
"""
from __future__ import annotations

import logging
import os
import warnings
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterable, Iterator

from ux_compose.dom import div

MODES = ("show", "hide", "raise")
ENV = "UX_COMPOSE_PLACEHOLDERS"
log = logging.getLogger("ux_compose.placeholder")
_logged: set[tuple[str, str, tuple[str, ...]]] = set()
_mode: ContextVar[str | None] = ContextVar("ux_compose_placeholder_mode", default=None)

CLASS_SHOW = (
    "rounded-xl border border-dashed border-amber-500 bg-amber-50 p-3 "
    "font-mono text-xs text-amber-900"
)


class MissingParams(TypeError):
    """A component rendered without required params in ``raise`` mode."""


class MissingParamsWarning(UserWarning):
    """A component rendered without required params in ``hide`` mode."""


def placeholder_mode() -> str:
    """Return the active mode: context override, then env, then ``hide``."""
    mode = _mode.get()
    if mode:
        return mode
    raw = os.environ.get(ENV, "").strip().lower()
    if not raw:
        return "hide"
    if raw not in MODES:
        raise ValueError(f"{ENV}={raw!r} is not one of {MODES}")
    return raw


@contextmanager
def use_placeholder_mode(mode: str) -> Iterator[None]:
    """Set the placeholder mode for the enclosed block (context-local)."""
    if mode not in MODES:
        raise ValueError(f"placeholder mode must be one of {MODES}, got {mode!r}")
    token = _mode.set(mode)
    try:
        yield
    finally:
        _mode.reset(token)


def _name(inst: Any) -> str:
    return type(inst).__name__


def placeholder_for(inst: Any, missing: Iterable[str]):
    """Build the visible placeholder node for ``inst`` (``show`` markup)."""
    names = sorted(missing)
    label = ", ".join(names)
    name = _name(inst)
    return div(
        f"{name} · missing: {label}",
        id=getattr(inst, "id", "") or name.lower(),
        role="note",
        aria_label=f"{name} placeholder: missing {label}",
        data_ux_placeholder=name,
        data_ux_missing=",".join(names),
        className=CLASS_SHOW,
    )


def render_missing(inst: Any, missing: Iterable[str]):
    """Return what the active mode renders for ``inst`` with ``missing`` params."""
    names = sorted(missing)
    mode = placeholder_mode()
    if mode == "raise":
        raise MissingParams(f"{_name(inst)} is missing required params: {', '.join(names)}")
    if mode == "show":
        return placeholder_for(inst, names)
    key = (type(inst).__module__, type(inst).__qualname__, tuple(names))
    if key not in _logged:
        _logged.add(key)
        log.warning(
            "%s rendered without required params: %s (placeholder hidden; "
            "set %s=show to see it)",
            _name(inst),
            ", ".join(names),
            ENV,
        )
    warnings.warn(
        f"{_name(inst)} rendered without required params: {', '.join(names)}",
        MissingParamsWarning,
        stacklevel=3,
    )
    return div(id=getattr(inst, "id", "") or _name(inst).lower(), hidden=True)


__all__ = [
    "MissingParams",
    "MissingParamsWarning",
    "placeholder_for",
    "placeholder_mode",
    "render_missing",
    "use_placeholder_mode",
]
