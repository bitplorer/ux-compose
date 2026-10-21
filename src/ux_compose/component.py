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

import functools
import inspect
from typing import Any, AsyncIterator

from ux_behavior import (  # type: ignore
    Component as _BehaviorComponent,
    MorphState,
    RefState,
    action,
)

from ux_dom.dom import Component as _DomComponent, dom_tag as _dom_tag  # type: ignore

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
        if "render" in cls.__dict__ and not hasattr(cls.__dict__["render"], "__ux_render__"):
            cls.render = _bind_render(cls.__dict__["render"])
        # Classes whose render takes params get the binding __init__ (spec §2);
        # zero-param classes keep the behavior base __init__ (no extra frame).
        if getattr(cls.render, "__ux_meta__", None) is not None and "__init__" not in cls.__dict__:
            cls.__init__ = _param_init
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
        from ux_compose.helpers import control as _control
        return _control(action_name, **args)

    def __render__(self, pretty: bool = False, **_kw) -> str:
        """Serialize live render() output. Always current MorphState, never a construct-time snapshot."""
        from ux_compose.helpers import _serialize_tree

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


_P = inspect.Parameter
_REQUIRED_KINDS = (_P.POSITIONAL_OR_KEYWORD, _P.KEYWORD_ONLY)


class _RenderMeta:
    """Signature facts for one ``render``, computed once per class."""

    __slots__ = ("names", "positional", "required", "var_kw", "simple", "sig")

    def __init__(self, fn) -> None:
        self.sig = inspect.signature(fn)
        params = list(self.sig.parameters.values())[1:]
        self.names = frozenset(p.name for p in params if p.kind in _REQUIRED_KINDS)
        self.positional = tuple(p.name for p in params if p.kind is _P.POSITIONAL_OR_KEYWORD)
        self.required = tuple(
            p.name for p in params if p.kind in _REQUIRED_KINDS and p.default is p.empty
        )
        self.var_kw = any(p.kind is _P.VAR_KEYWORD for p in params)
        self.simple = not any(p.kind in (_P.POSITIONAL_ONLY, _P.VAR_POSITIONAL) for p in params)


def _to_kwargs(owner: str, meta: _RenderMeta, args: tuple, kwargs: dict) -> tuple[tuple, dict]:
    """Normalise call args: positional → named kwargs (simple signatures)."""
    if not meta.simple:
        return args, kwargs
    if len(args) > len(meta.positional):
        raise TypeError(f"{owner}: takes {len(meta.positional)} positional params, got {len(args)}")
    out = dict(zip(meta.positional, args))
    for k, v in kwargs.items():
        if k in out:
            raise TypeError(f"{owner}: multiple values for {k!r}")
        if k not in meta.names and not meta.var_kw:
            raise TypeError(f"{owner}: unexpected keyword argument {k!r}")
        out[k] = v
    return (), out


def _param_init(self, *args: Any, **kwargs: Any) -> None:
    """Bind call-site args to ``render``'s signature (uidom pattern, spec §2).

    ``Tabs(items=[...])`` stores the args as kwargs; the outermost ``render()``
    replays them. Explicit ``render(...)`` args win.
    """
    _BehaviorComponent.__init__(self)
    if args or kwargs:
        meta = type(self).render.__ux_meta__
        name = type(self).__name__
        if meta.simple:
            _, self._ux_kwargs = _to_kwargs(name, meta, args, kwargs)
        else:
            try:
                bound = meta.sig.bind_partial(self, *args, **kwargs)
            except TypeError as exc:
                raise TypeError(f"{name}(...): {exc}") from None
            self._ux_args = tuple(bound.args[1:])
            self._ux_kwargs = dict(bound.kwargs)


def _bind_render(fn):
    """Wrap a subclass ``render`` so stored params replay once and gaps become placeholders."""
    meta = _RenderMeta(fn)
    if len(meta.sig.parameters) <= 1:
        fn.__ux_render__ = fn
        return fn
    required = meta.required

    @functools.wraps(fn)
    def render(self, *args, **kwargs):
        d = self.__dict__
        stored = d.get("_ux_kwargs")
        if stored is None and "_ux_args" not in d:
            # Hot path: nothing bound on this instance, so nothing to replay or leak.
            if required and not args:
                missing = [n for n in required if n not in kwargs]
                if missing:
                    from ux_compose.placeholder import render_missing

                    return render_missing(self, missing)
            return fn(self, *args, **kwargs)
        if d.get("_ux_in_render"):
            # super().render(...) inside an outer render: pass through untouched.
            return fn(self, *args, **kwargs)
        if meta.simple:
            if args:
                args, kwargs = _to_kwargs(type(self).__name__, meta, args, kwargs)
            if stored:
                kwargs = {**stored, **kwargs}
            if required:
                missing = [n for n in required if n not in kwargs]
                if missing:
                    from ux_compose.placeholder import render_missing

                    return render_missing(self, missing)
        else:
            if not args:
                args = d.get("_ux_args", ())
            if stored:
                kwargs = {**stored, **kwargs}
            if required:
                got = meta.sig.bind_partial(self, *args, **kwargs).arguments
                missing = [n for n in required if n not in got]
                if missing:
                    from ux_compose.placeholder import render_missing

                    return render_missing(self, missing)
        d["_ux_in_render"] = True
        try:
            return fn(self, *args, **kwargs)
        finally:
            d["_ux_in_render"] = False

    render.__ux_render__ = fn
    render.__ux_meta__ = meta
    return render


def _mro_collision_msg(cls: type, base: type) -> str:
    return (
        f"{cls.__qualname__} must not inherit {base.__module__}.{base.__name__}. "
        "render() returns ux-dom tags; the live unit is Behavior. "
        "A shared MRO collides with tree verbs (add/remove/get/clear) now or later."
    )


__all__ = ["Component", "MorphState", "RefState", "action"]
