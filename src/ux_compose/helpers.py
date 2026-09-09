"""Composition algebra — bind / control / notify / update_with / morph_play.

Not author convenience (that is ``author.py``). Not GET brand (``chrome.py``).
Not a Document serialize clone: ``_fragment_for_target`` is the morph
safety net owned by ``update_with``.

Never import ux_channel or CEK. XOR and Morph-then-Play are enforced by
construction where possible; remaining cases fail closed under doctor.

Helpers emit real ux-behavior Op objects (hard dependency, Python ≥3.14).
"""
from __future__ import annotations

import json
import re
from typing import Any, List, Optional

from ux_behavior import bind as _behavior_bind, notify as _real_notify, update as _real_update
from ux_behavior.ops import Op as _Op
from ux_dom.response.serialize import to_html_bytes


def _as_op(ns: str, name: str, payload: Optional[dict] = None) -> Any:
    """Build a real ux-behavior Op. Compose does not emit parallel dict Ops."""
    return _Op(ns=ns, name=name, payload=payload or {})


def notify(message: str, **kwargs) -> Any:
    """Emit a notify / toast Op as data (ux-behavior.notify)."""
    level = kwargs.pop("level", "info")
    return _real_notify(message, level=level)


def _live_channel() -> Any:
    """Isolation: Channel instance from App.use_channel, never ux_channel import."""
    try:
        from ux_compose.wire.caps import live_channel

        return live_channel()
    except Exception:
        return None


def _minted_attrs(verb: str, args: dict) -> dict | None:
    channel = _live_channel()
    if channel is None:
        return None
    from ux_compose.wire.caps import control_attrs

    minted = control_attrs(channel, verb, **args)
    cap = str(minted.get("data-channel-cap") or "").strip()
    if not cap:
        raise RuntimeError(
            f"live Channel mint for {verb!r} returned empty Cap; "
            "refusing no-cap attrs (Cap Host would toast missing capability)"
        )
    return minted


def bind(action_obj, **kwargs):
    """Symbol-safe UI attrs via ux-behavior.bind.

    String verbs stay compose ``control()`` orchestration (Cap mint through
    ``wire.caps``). @action methods use ux-behavior — no parallel bind.
    When Cap Host is live, mint via ``wire.caps.control_attrs``. Empty mint
    fails loud.
    """
    if isinstance(action_obj, str):
        return _action_attrs(action_obj, kwargs)
    attrs = _behavior_bind(action_obj, **kwargs)
    verb = attrs.get("data-ux-action") or attrs.get("data-channel-action")
    if verb:
        minted = _minted_attrs(str(verb), kwargs)
        if minted is not None:
            merged = dict(attrs)
            merged.update(minted)
            return merged
        out = dict(attrs)
        out.setdefault("data-channel-action", str(verb))
        return out
    return attrs


def _action_attrs(verb: str, args: dict) -> dict:
    """Mirror ``ux_behavior.action_ui_attrs``: both progressive and live names.

    ``data-ux-action`` is the L1/offline stamp. ``data-channel-action`` is
    what ``ux-channel.js`` click-binds. When a live Channel is registered,
    mint ``data-channel-cap`` via wire.caps (no ``ux_channel`` import).
    """
    minted = _minted_attrs(verb, args)
    if minted is not None:
        return minted
    attrs = {"data-ux-action": verb, "data-channel-action": verb}
    if args:
        attrs["data-channel-args"] = json.dumps(
            {k: str(v) for k, v in args.items()},
            separators=(",", ":"),
            ensure_ascii=True,
        )
    for k, v in args.items():
        attrs[f"data-ux-arg-{k}"] = str(v)
    return attrs


def control(action: str, **args) -> dict:
    """Progressive control attrs (string action name). Prefer bind() / .ui in new code."""
    return _action_attrs(action, args)


def _serialize_tree(tree: Any) -> str:
    """Serialize via ux-dom. No homemade HTML-string renderer."""
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    return to_html_bytes(tree).decode("utf-8")


_VOID_TAGS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }
)
_TAG_NAME = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9:_-]*)", re.I)
_ID_ATTR_NAME = re.compile(r"(?<![A-Za-z0-9:_-])id\s*=\s*", re.I)


def _skip_quoted(html: str, start: int) -> int:
    """Advance from ``start`` (a ``>`` search) past the next unquoted ``>``."""
    i = start
    in_quote: str | None = None
    while i < len(html):
        c = html[i]
        if in_quote:
            if c == in_quote:
                in_quote = None
        elif c in "\"'":
            in_quote = c
        elif c == ">":
            return i
        i += 1
    return -1


def _element_end(html: str, start: int) -> int | None:
    """Exclusive index of the element that opens at ``html[start]`` (``<``)."""
    m = _TAG_NAME.match(html, start)
    if not m or m.group(1):
        return None
    name = m.group(2).lower()
    gt = _skip_quoted(html, m.end())
    if gt < 0:
        return None
    self_close = gt > start and html[gt - 1] == "/"
    after_open = gt + 1
    if self_close or name in _VOID_TAGS:
        return after_open
    depth = 1
    i = after_open
    while i < len(html):
        if html.startswith("<!--", i):
            end = html.find("-->", i + 4)
            if end < 0:
                return None
            i = end + 3
            continue
        if html[i] != "<":
            i += 1
            continue
        tm = _TAG_NAME.match(html, i)
        if not tm:
            i += 1
            continue
        gt = _skip_quoted(html, tm.end())
        if gt < 0:
            return None
        tname = tm.group(2).lower()
        closing = bool(tm.group(1))
        self_close = gt > i and html[gt - 1] == "/"
        nxt = gt + 1
        if tname == name:
            if closing:
                depth -= 1
                if depth == 0:
                    return nxt
            elif not self_close and name not in _VOID_TAGS:
                depth += 1
        i = nxt
    return None


def _open_tag_id(open_tag: str) -> str | None:
    """Return the ``id`` attribute of one start tag, ignoring quoted values."""
    i = 0
    in_quote: str | None = None
    while i < len(open_tag):
        c = open_tag[i]
        if in_quote:
            if c == in_quote:
                in_quote = None
            i += 1
            continue
        if c in "\"'":
            in_quote = c
            i += 1
            continue
        m = _ID_ATTR_NAME.match(open_tag, i)
        if not m:
            i += 1
            continue
        j = m.end()
        if j < len(open_tag) and open_tag[j] in "\"'":
            q = open_tag[j]
            k = open_tag.find(q, j + 1)
            return open_tag[j + 1 : k] if k >= 0 else open_tag[j + 1 :].rstrip(">/ \t\n\r")
        k = j
        while k < len(open_tag) and open_tag[k] not in " \t\n\r>/":
            k += 1
        return open_tag[j:k]
    return None


def _fragment_for_target(html: str, target_id: str) -> str:
    """Document law: morph payload is the subtree for ``#target``, not a shell.

    Authors should still write fragment ``render()``. This strip is a safety
    net when ``render()`` returns a full shell that *contains* ``#target``.
    Already-fragment HTML (root id == target) is returned unchanged. Missing
    target id leaves ``html`` as-is.
    """
    blob = html or ""
    tid = str(target_id or "").lstrip("#")
    if not blob or not tid:
        return html
    i = 0
    while i < len(blob):
        if blob.startswith("<!--", i):
            end = blob.find("-->", i + 4)
            i = len(blob) if end < 0 else end + 3
            continue
        if blob[i] != "<" or blob.startswith(("</", "<!", "<?"), i):
            i += 1
            continue
        gt = _skip_quoted(blob, i + 1)
        if gt < 0:
            break
        if _open_tag_id(blob[i : gt + 1]) == tid:
            end = _element_end(blob, i)
            if end is not None:
                return blob[i:end]
        i = gt + 1
    return html


def _render_html(component_or_id: Any, *, target_id: str | None = None) -> str:
    if isinstance(component_or_id, str):
        html = component_or_id
    else:
        render = getattr(component_or_id, "render", None)
        tree = render() if callable(render) else component_or_id
        html = _serialize_tree(tree)
    tid = target_id
    if not tid:
        raw = getattr(component_or_id, "id", None)
        if raw:
            tid = str(raw)
    if tid:
        return _fragment_for_target(html, tid)
    return html


def _coerce_op(op: Any) -> Any:
    if op is None:
        return None
    if isinstance(op, _Op):
        return op
    if isinstance(op, dict):
        return op
    if hasattr(op, "ns") and hasattr(op, "name"):
        return op
    return op


def _looks_like_op(op: Any) -> bool:
    if op is None:
        return False
    if isinstance(op, _Op):
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

    Morph HTML for ``#target`` is the fragment rooted at that id. Authors
    should still write fragment ``render()``; helpers strip an outer shell
    when the rendered tree contains an element matching ``component.id``.
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
        morph_payload["html"] = _fragment_for_target(html, tid)
    else:
        morph_payload["html"] = _render_html(component, target_id=tid)
    # strip helper kwargs that are not morph fields
    for k, v in kwargs.items():
        if k not in ("extra_ops",):
            morph_payload[k] = v

    ops: List[Any] = [_real_update(tid, morph_payload.get("html", ""))]
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
    ops: List[Any] = [_real_update(tid, "")]
    ops.extend(_normalize_plan_ops(plan))
    return ops


__all__ = ["notify", "control", "bind", "update_with", "morph_play"]
