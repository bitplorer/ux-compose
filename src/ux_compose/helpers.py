"""
High-level helpers that emit pure Ops / Plans and enforce the Composition Algebra.

Never import ux_channel or CEK. XOR and Morph-then-Play are enforced by construction
where possible; remaining cases fail closed under doctor / strict mode.

When ux-behavior is installed, helpers emit real Op objects (required by @action).
When absent, helpers emit plain dict Ops for the pure-shim path.
"""
from __future__ import annotations

from typing import Any, Iterable, List, Optional

# Prefer real specialist Ops when available
try:
    from ux_behavior import notify as _real_notify, update as _real_update
    from ux_behavior.ops import Op as _Op
    _HAS_BEHAVIOR = True
except ImportError:
    _real_notify = _real_update = _Op = None  # type: ignore
    _HAS_BEHAVIOR = False


def _as_op(ns: str, name: str, payload: Optional[dict] = None) -> Any:
    """Build a real Op when behavior is present, else a plain dict."""
    payload = payload or {}
    if _HAS_BEHAVIOR and _Op is not None:
        return _Op(ns=ns, name=name, payload=payload)
    return {"op": f"{ns}.{name}" if ns else name, **payload}


def notify(message: str, **kwargs) -> Any:
    """Emit a notify / toast Op as data."""
    if _HAS_BEHAVIOR and _real_notify is not None:
        level = kwargs.pop("level", "info")
        return _real_notify(message, level=level)
    return {"op": "notify", "message": message, **kwargs}


def bind(action_obj, **kwargs):
    """Symbol-safe UI attrs. Prefers ux_behavior.bind / .ui when available."""
    try:
        from ux_behavior.action import bind as _b
        return _b(action_obj, **kwargs)
    except Exception:
        pass
    ui = getattr(action_obj, "ui", None)
    if callable(ui):
        try:
            return ui(**kwargs)
        except Exception:
            pass
    if isinstance(action_obj, str):
        verb = action_obj
    elif callable(action_obj):
        name = getattr(action_obj, "__name__", "action")
        inst = getattr(action_obj, "__self__", None)
        if inst is not None:
            sid = getattr(inst, "id", None) or type(inst).__name__.lower()
            verb = f"{sid}.{name}"
        else:
            verb = str(name)
    else:
        raise TypeError(
            f"bind requires @action method or str, got {type(action_obj).__name__}"
        )
    attrs = {"data-ux-action": verb}
    for k, v in kwargs.items():
        attrs[f"data-ux-arg-{k}"] = str(v)
    return attrs


def control(action: str, **args) -> dict:
    """Progressive control attrs. Offline: plain data-*. Live: upgraded by Channel."""
    attrs = {"data-ux-action": action}
    for k, v in args.items():
        attrs[f"data-ux-arg-{k}"] = str(v)
    return attrs


def update_with(component: Any, *fields: str, **kwargs) -> Any:
    """Morph-then-update helper. Emits update Op for component fields."""
    if _HAS_BEHAVIOR and _real_update is not None:
        return _real_update(component, *fields, **kwargs)
    target = getattr(component, "id", None) or getattr(component, "__name__", "component")
    payload = {"target": f"#{target}", "fields": list(fields), **kwargs}
    return _as_op("", "update", payload)


def morph_play(component: Any, plan: Any = None, **kwargs) -> list:
    """Morph-then-Play: morph target then optional motion plan."""
    target = getattr(component, "id", None) or "component"
    ops: List[Any] = [
        _as_op("", "morph", {"target": f"#{target}", "strategy": kwargs.get("strategy", "idiomorph")})
    ]
    if plan is not None:
        if isinstance(plan, list):
            ops.extend(plan)
        else:
            ops.append(plan)
    return ops


__all__ = ["notify", "control", "bind", "update_with", "morph_play"]
