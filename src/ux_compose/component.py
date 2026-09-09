"""
Unified Component — inevitable author surface.

Satisfies the ux-behavior Component protocol (MorphState / RefState / @action)
and produces renderable trees for ux-dom. Composition is internal; authors
never see dual inheritance.

render() returns a ux-dom tag tree (div, h1, …). ux-dom is a hard
dependency (Python ≥3.14).

This class does **not** subclass ux-dom Component. Freeze on that class is
fragile (skip __init__, republish _entry). The MRO is not: add/remove/get/clear
are reserved tree verbs today, and more will land. Sharing that MRO with
@action names collides now or later. Tags are the return type of render().
"""
from __future__ import annotations

from typing import AsyncIterator

from ux_behavior import (  # type: ignore
    Component as _BehaviorComponent,
    MorphState,
    RefState,
    action,
)

from ux_dom.dom.src.component import Component as _DomComponent  # type: ignore
from ux_dom.dom.src.dom_tag import dom_tag as _dom_tag  # type: ignore

_DOM_TREE_NAMES = frozenset({"Component", "Tags", "dom_tag", "ReactiveComponent", "Fragment"})


class Component(_BehaviorComponent):
    """
    Unified Component.

    - id: stable target for morph + motion (default ClassName.lower(); override with id=)
    - MorphState fields: dirty → morph unit
    - RefState fields: silent memory
    - render() → ux-dom tree. Prefer tags::

          return div(h1(f"{self.count}"), id=self.id)

    - @action(caps=...) methods return None | list[Op] | Result
    - control() via helpers for progressive attrs
    - __render__(pretty=False) re-runs render() — never a construct snapshot
    - __async_render__ yields that HTML for StreamingResponse / page-route plane

    Return semantics (hard contract from the mental model):
    1. return None → auto-morph dirty MorphStates
    2. return list[Op] → exact Ops (auto suppressed)
    3. transition.play / scene targeting a dirty id suppresses that auto-morph
    4. enter(..., html=...) suppresses morph for that target (XOR)
    5. Prefer update_with(self, scene(...)) for morph + motion
    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # Auto-id when class body omitted id= (behavior base also does this)
        if "id" not in cls.__dict__ and not getattr(cls, "id", ""):
            cls.id = cls.__name__.lower()
        for base in cls.__mro__:
            if base is cls or base is Component or base is _BehaviorComponent or base is object:
                continue
            mod = getattr(base, "__module__", "") or ""
            if base is _DomComponent or base is _dom_tag:
                raise TypeError(_mro_collision_msg(cls, base))
            if mod.startswith("ux_dom.dom") and base.__name__ in _DOM_TREE_NAMES:
                raise TypeError(_mro_collision_msg(cls, base))

    def control(self, action_name: str, **args) -> dict:
        """Progressive control attrs. Delegates to helpers.control."""
        from ux_compose.algebra import control as _control
        return _control(action_name, **args)

    def dirty_fields(self) -> set:
        # Real MorphState dirty tracking is internal; expose a best-effort set
        return set(getattr(self, "_dirty", set()))

    def clear_dirty(self) -> None:
        if hasattr(self, "_dirty"):
            self._dirty.clear()

    def __render__(self, pretty: bool = False, **_kw) -> str:
        """Serialize live render() output. Always current MorphState, never a construct-time snapshot."""
        from ux_compose.algebra import _serialize_tree

        tree = self.render()
        if pretty and tree is not None and not isinstance(tree, str):
            return str(tree)
        return _serialize_tree(tree)

    async def __async_render__(self, pretty: bool = False, **_kw) -> AsyncIterator[str]:
        """Async HTML stream for StreamingResponse / page-route plane.

        Yields the live string from ``__render__`` (single chunk). This lets
        endpoints return a Compose Component instance and still be accepted by
        ``streaming_response`` the same way a ``dom_tag`` is.
        """
        yield self.__render__(pretty=pretty)


def _mro_collision_msg(cls: type, base: type) -> str:
    return (
        f"{cls.__qualname__} must not inherit {base.__module__}.{base.__name__}. "
        "render() returns ux-dom tags; the live unit is Behavior. "
        "A shared MRO collides with tree verbs (add/remove/get/clear) now or later."
    )


__all__ = ["Component", "MorphState", "RefState", "action"]
