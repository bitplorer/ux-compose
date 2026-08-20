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


def control(action: str, **args) -> dict:
    """Progressive control attrs. Offline: plain data-*. Live: upgraded by Channel."""
    attrs = {"data-ux-action": action}
    for k, v in args.items():
        attrs[f"data-ux-arg-{k}"] = str(v)
    return attrs


def _serialize_tree(tree: Any) -> str:
    """Serialize a render() result: ux-dom trees via __render__(pretty=False)."""
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    if isinstance(tree, bytes):
        return tree.decode("utf-8", errors="replace")
    to_render = getattr(tree, "__render__", None)
    if callable(to_render):
        try:
            return str(to_render(pretty=False))
        except TypeError:
            try:
                return str(to_render())
            except Exception:
                pass
        except Exception:
            pass
    return str(tree)


def _render_html(component_or_id: Any) -> str:
    """Best-effort render of a Component instance to an HTML string."""
    if component_or_id is None or isinstance(component_or_id, str):
        return ""
    render = getattr(component_or_id, "render", None)
    if not callable(render):
        return ""
    try:
        tree = render()
    except Exception:
        return ""
    return _serialize_tree(tree)


def update_with(
    component_or_id: Any,
    scene_or_plan: Any = None,
    *,
    extra_ops: Optional[Iterable] = None,
    html: Any = None,
) -> List[Any]:
    """Recommended path when combining MorphState mutation with motion.

    Emits correct ordered Ops, enforces XOR by construction, preserves Morph-then-Play.
    Always returns list[Op] (real) or list[dict] (shim) — never mixed when behavior present.

    When *component_or_id* is a Component instance, its ``render()`` output is used as
    the morph patch (real HTML) unless *html* is passed explicitly.
    ux-dom trees are serialized with ``__render__(pretty=False)``.
    """
    ops: List[Any] = []

    target = None
    if hasattr(component_or_id, "id"):
        target = getattr(component_or_id, "id", None) or None
    elif isinstance(component_or_id, str):
        target = component_or_id.lstrip("#") or None

    if target:
        if html is not None:
            patch = html if isinstance(html, str) else _serialize_tree(html)
        else:
            patch = _render_html(component_or_id)
        if _HAS_BEHAVIOR and _real_update is not None:
            ops.append(_real_update(target, html=patch if patch is not None else ""))
        else:
            op: dict = {
                "op": "morph",
                "target": f"#{target}",
                "strategy": "idiomorph",
            }
            if patch:
                op["html"] = patch
            ops.append(op)

    if scene_or_plan is not None:
        plan_ops = _normalize_plan_ops(scene_or_plan)
        ops.extend(plan_ops)

    if extra_ops:
        for op in extra_ops:
            if op is not None:
                ops.append(_coerce_op(op))

    return ops


def _coerce_op(op: Any) -> Any:
    """Ensure Op objects when behavior is present; leave dicts for shim."""
    if op is None:
        return op
    if _HAS_BEHAVIOR and _Op is not None:
        if isinstance(op, _Op):
            return op
        if isinstance(op, dict):
            if op.get("op") == "transition.play" or "plan" in op:
                plan = op.get("plan", op)
                return _Op(
                    ns="transition",
                    name="play",
                    payload={"plan": plan}
                    if "plan" in op or op.get("op") == "transition.play"
                    else op,
                )
            name = op.get("op") or op.get("name") or "custom"
            if "." in str(name):
                ns, _, nm = str(name).partition(".")
                return _Op(
                    ns=ns,
                    name=nm,
                    payload={k: v for k, v in op.items() if k not in ("op", "name")},
                )
            return _Op(
                ns="ui",
                name=str(name),
                payload={k: v for k, v in op.items() if k != "op"},
            )
    return op


def _normalize_plan_ops(scene_or_plan: Any) -> List[Any]:
    """Turn a scene builder / play result / plan into list of transition.play Ops."""
    if scene_or_plan is None:
        return []

    # Scene.play() → {'ok': True, 'ops': [dict, ...]}
    if (
        isinstance(scene_or_plan, dict)
        and "ops" in scene_or_plan
        and scene_or_plan.get("ok") is not None
    ):
        return [_coerce_op(o) for o in scene_or_plan.get("ops") or []]

    if isinstance(scene_or_plan, dict):
        if scene_or_plan.get("op") == "transition.play" or "plan" in scene_or_plan:
            return [_coerce_op(scene_or_plan)]
        return [_coerce_op({"op": "transition.play", "plan": scene_or_plan})]

    if hasattr(scene_or_plan, "play"):
        try:
            result = scene_or_plan.play()
            return _normalize_plan_ops(result)
        except Exception:
            pass

    if hasattr(scene_or_plan, "plan"):
        try:
            plan = scene_or_plan.plan()
            return [_coerce_op({"op": "transition.play", "plan": plan})]
        except Exception:
            pass

    return [_coerce_op({"op": "transition.play", "plan": scene_or_plan})]


def morph_play(target: str, plan: Any) -> List[Any]:
    return update_with(target, plan)


__all__ = ["notify", "control", "update_with", "morph_play"]
