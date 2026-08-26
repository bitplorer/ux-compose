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
    """Progressive control attrs (string action name). Prefer bind() / .ui in new code."""
    attrs = {"data-ux-action": action}
    for k, v in args.items():
        attrs[f"data-ux-arg-{k}"] = str(v)
    return attrs


def _serialize_tree(tree: Any) -> str:
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


def _looks_like_op(op: Any) -> bool:
    if op is None:
        return False
    if _HAS_BEHAVIOR and _Op is not None and isinstance(op, _Op):
        return True
    if isinstance(op, dict) and str(op.get("op", "")).endswith("play"):
        return True
    if isinstance(op, dict) and op.get("op") in ("morph", "notify", "toast"):
        return True
    if type(op).__name__ in {"Scene", "Plan"}:
        return False
    if hasattr(op, "ns") and hasattr(op, "name") and hasattr(op, "payload"):
        return True
    return False


def _as_play(plan: Any) -> Any:
    return _as_op("transition", "play", {"plan": plan})


def _normalize_plan_ops(scene_or_plan: Any) -> List[Any]:
    """Turn a Scene / Plan / Op into one ``transition.play``.

    Motion IR is data. ``Scene.ops()`` is Channel wire shape — not Behavior
    Ops. Wrap the compiled plan so @action returns list[Op].
    """
    if scene_or_plan is None:
        return []
    if isinstance(scene_or_plan, list):
        out: List[Any] = []
        for item in scene_or_plan:
            out.extend(_normalize_plan_ops(item))
        return out
    if _looks_like_op(scene_or_plan):
        if isinstance(scene_or_plan, dict) and str(scene_or_plan.get("op", "")).endswith("play"):
            return [_as_play(scene_or_plan.get("plan", scene_or_plan))]
        coerced = _coerce_op(scene_or_plan)
        return [coerced] if coerced is not None else []
    if isinstance(scene_or_plan, dict):
        return [_as_play(scene_or_plan.get("plan", scene_or_plan))]
    compiled = scene_or_plan
    for attr in ("plan", "to_plan"):
        val = getattr(scene_or_plan, attr, None)
        if callable(val):
            try:
                compiled = val()
                break
            except Exception:
                pass
        elif val is not None and val is not scene_or_plan:
            compiled = val
            break
    return [_as_play(compiled)]


def update_with(
    component: Any,
    plan: Any = None,
    *fields: str,
    html: Optional[str] = None,
    strategy: str = "idiomorph",
    extra_ops: Optional[list] = None,
    **kwargs: Any,
) -> List[Any]:
    """Morph-then-Play helper used from @action methods.

    Returns an ordered list: morph Op first, then plan ops, then extra_ops.
    XOR: never puts html= on the plan for the same target as the morph.
    """
    target = getattr(component, "id", None) or getattr(
        component, "__name__", component if isinstance(component, str) else "component"
    )
    tid = f"#{target}" if not str(target).startswith("#") else str(target)

    morph_payload: dict[str, Any] = {
        "target": tid,
        "strategy": strategy,
    }
    if fields:
        morph_payload["fields"] = list(fields)
    if html is not None:
        morph_payload["html"] = html
    else:
        try:
            morph_payload["html"] = _render_html(component)
        except Exception:
            pass
    # strip helper kwargs that are not morph fields
    for k, v in kwargs.items():
        if k not in ("extra_ops",):
            morph_payload[k] = v

    if _HAS_BEHAVIOR and _real_update is not None:
        ops: List[Any] = [_real_update(tid, morph_payload.get("html", ""))]
    else:
        ops = [_as_op("", "morph", morph_payload)]
    ops.extend(_normalize_plan_ops(plan))
    if extra_ops:
        for o in extra_ops:
            c = _coerce_op(o)
            if c is not None:
                ops.append(c)
    return ops


def morph_play(target: str, plan: Any) -> List[Any]:
    """Morph-then-Play: morph target, then append motion plan ops."""
    tid = target if str(target).startswith("#") else f"#{target}"
    if _HAS_BEHAVIOR and _real_update is not None:
        ops: List[Any] = [_real_update(tid, "")]
    else:
        ops = [_as_op("", "morph", {"target": tid, "strategy": "idiomorph"})]
    ops.extend(_normalize_plan_ops(plan))
    return ops


__all__ = ["notify", "control", "bind", "update_with", "morph_play"]
