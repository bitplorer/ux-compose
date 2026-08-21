"""
High-level helpers that emit pure Ops / Plans and enforce the Composition Algebra.

Never import ux_channel or CEK. XOR and Morph-then-Play are enforced by construction
where possible; remaining cases fail closed under doctor / strict mode.

When ux-behavior is installed, helpers emit real Op objects (required by @action).
When absent, helpers emit plain dict Ops for the pure-shim path.
"""
from __future__ import annotations

from typing import Any, List, Optional

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
    """Symbol-safe UI attrs. Prefers ux_behavior.bind / .ui when available.

    Progressive attrs: data-ux-action + data-ux-arg-*.
    Keep control(str) for stringly escape hatch; prefer bind / .ui in product code.
    """
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
    """Progressive control attrs (string action name). Prefer bind() / .ui in new code."""
    attrs = {"data-ux-action": action}
    for k, v in args.items():
        attrs[f"data-ux-arg-{k}"] = str(v)
    return attrs


def _serialize_tree(tree: Any) -> str:
    """Best-effort HTML serialization for Component.__render__ / morph payloads."""
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    for attr in ("render", "__render__", "__html__", "to_html"):
        fn = getattr(tree, attr, None)
        if callable(fn):
            try:
                out = fn()
                if out is not None and out is not tree:
                    return _serialize_tree(out)
            except TypeError:
                try:
                    return _serialize_tree(fn(tree))  # type: ignore[misc]
                except Exception:
                    pass
            except Exception:
                pass
    try:
        return str(tree)
    except Exception:
        return ""


def _render_html(component_or_id: Any) -> str:
    if isinstance(component_or_id, str):
        return component_or_id
    render = getattr(component_or_id, "render", None)
    if callable(render):
        try:
            return _serialize_tree(render())
        except Exception:
            pass
    return _serialize_tree(component_or_id)


def update_with(
    component: Any,
    *fields: str,
    html: Optional[str] = None,
    strategy: str = "idiomorph",
    **kwargs: Any,
) -> Any:
    """Morph / update helper used from @action methods.

    When ux-behavior is present, prefer specialist update().
    Otherwise emit a morph-oriented Op dict.
    """
    if _HAS_BEHAVIOR and _real_update is not None:
        try:
            return _real_update(component, *fields, **kwargs)
        except Exception:
            pass

    target = getattr(component, "id", None) or getattr(
        component, "__name__", "component"
    )
    payload: dict[str, Any] = {
        "target": f"#{target}" if not str(target).startswith("#") else str(target),
        "strategy": strategy,
    }
    if fields:
        payload["fields"] = list(fields)
    if html is not None:
        payload["html"] = html
    else:
        try:
            payload["html"] = _render_html(component)
        except Exception:
            pass
    payload.update(kwargs)
    return _as_op("", "morph", payload)


def _coerce_op(op: Any) -> Any:
    if op is None:
        return None
    if _HAS_BEHAVIOR and _Op is not None and isinstance(op, _Op):
        return op
    if isinstance(op, dict):
        return op
    if hasattr(op, "ns") and hasattr(op, "name"):
        return op
    return op


def _normalize_plan_ops(scene_or_plan: Any) -> List[Any]:
    if scene_or_plan is None:
        return []
    if isinstance(scene_or_plan, list):
        return [o for o in (_coerce_op(x) for x in scene_or_plan) if o is not None]
    for attr in ("ops", "plan", "to_ops"):
        val = getattr(scene_or_plan, attr, None)
        if callable(val):
            try:
                return _normalize_plan_ops(val())
            except Exception:
                pass
        elif isinstance(val, list):
            return _normalize_plan_ops(val)
    coerced = _coerce_op(scene_or_plan)
    return [coerced] if coerced is not None else []


def morph_play(target: str, plan: Any) -> List[Any]:
    """Morph-then-Play: morph target, then append motion plan ops."""
    tid = target if str(target).startswith("#") else f"#{target}"
    ops: List[Any] = [
        _as_op("", "morph", {"target": tid, "strategy": "idiomorph"})
    ]
    ops.extend(_normalize_plan_ops(plan))
    return ops


__all__ = ["notify", "control", "bind", "update_with", "morph_play"]
