"""
Unified Component — inevitable author surface.

Satisfies the ux-behavior Component protocol (MorphState / RefState / @action)
and produces renderable trees for ux-dom. Composition is internal; authors
never see dual inheritance.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

# Prefer real specialists when installed.
try:
    from ux_behavior import (  # type: ignore
        Component as _BehaviorComponent,
        MorphState,
        RefState,
        action,
    )
    _HAS_BEHAVIOR = True
except ImportError:  # pragma: no cover
    _HAS_BEHAVIOR = False

    class MorphState:  # type: ignore
        def __init__(self, default: Any = None):
            self.default = default
            self._name: Optional[str] = None

        def __set_name__(self, owner, name):
            self._name = name

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            return obj.__dict__.get(self._name, self.default)

        def __set__(self, obj, value):
            obj.__dict__[self._name] = value
            dirty = obj.__dict__.setdefault("_dirty", set())
            dirty.add(self._name)

    class RefState:  # type: ignore
        def __init__(self, default: Any = None):
            self.default = default
            self._name: Optional[str] = None

        def __set_name__(self, owner, name):
            self._name = name

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self
            return obj.__dict__.get(self._name, self.default)

        def __set__(self, obj, value):
            obj.__dict__[self._name] = value

    def action(caps=()):  # type: ignore
        def deco(fn: Callable):
            fn._ux_action = True  # type: ignore
            fn._ux_caps = caps  # type: ignore
            return fn
        return deco

    class _BehaviorComponent:  # type: ignore
        id: str = ""

        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

        def render(self):
            raise NotImplementedError


class Component(_BehaviorComponent):
    """
    Unified Component.

    - id: stable target for morph + motion
    - MorphState fields: dirty → morph unit
    - RefState fields: silent memory
    - render() → ux-dom tree (or object with __render__)
    - @action(caps=...) methods return None | list[Op] | Result
    - control() via helpers for progressive attrs

    Return semantics (hard contract from the mental model):
    1. return None → auto-morph dirty MorphStates
    2. return list[Op] → exact Ops (auto suppressed)
    3. transition.play / scene targeting a dirty id suppresses that auto-morph
    4. enter(..., html=...) suppresses morph for that target (XOR)
    5. Prefer update_with(self, scene(...)) for morph + motion
    """

    # Real Behavior Component already has id; we only ensure the attribute exists
    # for the shim path and for static analysis.
    if not _HAS_BEHAVIOR:
        id: str = ""

    def control(self, action_name: str, **args) -> dict:
        """Progressive control attrs. Delegates to helpers.control."""
        from ux_compose.helpers import control as _control
        return _control(action_name, **args)

    def dirty_fields(self) -> set:
        # Real MorphState dirty tracking is internal; expose a best-effort set
        return set(getattr(self, "_dirty", set()))

    def clear_dirty(self) -> None:
        if hasattr(self, "_dirty"):
            self._dirty.clear()


__all__ = ["Component", "MorphState", "RefState", "action"]
