"""Live Cap mint + Intent submit.

Isolation door only — product code never imports ux_channel. Authors reach
this through App.mint_cap / App.submit_intent (thin wrap) or this module.

Cap Law: Channel verifies the Cap at the edge; Behavior.dispatch after attach
is Host-internal (specialist contract — do not change Behavior).
"""

from __future__ import annotations

import asyncio
import json
from contextvars import ContextVar
from typing import Any, Mapping, Optional

from ux_compose.dom import html_text
from ux_compose.helpers import _require_control_arg_names
from ux_compose.visitor import current_subject

_PROCESS_CHANNEL: Any = None
_LIVE: ContextVar[Any] = ContextVar("ux_compose_live_channel", default=None)


def register_live_channel(channel: Any) -> None:
    """Process + ContextVar registry so helpers.control can mint without App in scope.

    Set from ``App.use_channel``. ``channel=None`` clears the live door
    (offline helpers keep dual action attrs, no Cap).
    """
    global _PROCESS_CHANNEL
    _PROCESS_CHANNEL = channel
    _LIVE.set(channel)


def live_channel() -> Any:
    """Return the Channel registered by ``App.use_channel``, or None."""
    ctx = _LIVE.get()
    if ctx is not None:
        return ctx
    return _PROCESS_CHANNEL


def _hyphenate_keys(mapping: Mapping[str, Any]) -> dict[str, str]:
    return {str(k).replace("_", "-"): str(v) for k, v in mapping.items()}


def _cap_token(raw: Mapping[str, Any]) -> str:
    return str(raw.get("data-channel-cap") or "").strip()


def _as_attr_map(result: Any) -> dict[str, str]:
    if result is None:
        return {}
    if isinstance(result, Mapping):
        return _hyphenate_keys(result)
    as_dict = getattr(result, "as_dict", None)
    if callable(as_dict):
        raw = as_dict()
        if isinstance(raw, Mapping):
            return _hyphenate_keys(raw)
    as_ux = getattr(result, "as_ux_dom", None)
    if callable(as_ux):
        raw = as_ux()
        if isinstance(raw, Mapping):
            return _hyphenate_keys(raw)
    return {}


def _call_control(
    control_fn: Any, action: str, args: Mapping[str, Any], bind: Mapping[str, str]
) -> Any:
    payload = dict(args)
    try:
        return control_fn(action, trust=payload if payload else None, **bind)
    except TypeError:
        pass
    try:
        return control_fn(action, **bind, **payload)
    except TypeError:
        return control_fn(action, **bind)


def control_attrs(channel: Any, action: str, /, **args: Any) -> dict[str, str]:
    """Mint Channel control attrs for *action*; merge progressive data-ux-*.

    Isolation door: duck-type ``channel.control(action, …).as_dict()``
    (underscore keys become hyphen). If ``control`` is absent, duck-type
    ``channel.mint``. Never re-implements Cap crypto.

    The Cap is bound to the request's visitor (``sub=``), so only that
    visitor can spend it. Outside a request the Cap names no subject.
    """
    subject = current_subject()
    bind = {"sub": subject} if subject else {}
    _require_control_arg_names(args)
    if channel is None:
        raise RuntimeError(
            "control_attrs requires a live Channel. Call App.use_channel() first "
            "(Level 2). Offline Level 1 has no Caps to mint."
        )
    raw: dict[str, str] = {}
    control_fn = getattr(channel, "control", None)
    if callable(control_fn):
        try:
            raw = _as_attr_map(_call_control(control_fn, str(action), args, bind))
        except Exception:
            raw = {}
    if not _cap_token(raw):
        mint_fn = getattr(channel, "mint", None)
        if callable(mint_fn):
            token = str(mint_fn(str(action), dict(args), **bind) or "").strip()
            if token:
                raw.setdefault("data-channel-action", str(action))
                raw["data-channel-cap"] = token
                if args and "data-channel-args" not in raw:
                    raw["data-channel-args"] = json.dumps(
                        {k: str(v) for k, v in args.items()},
                        separators=(",", ":"),
                        ensure_ascii=True,
                    )
        elif not raw:
            raise TypeError(
                "channel has no control() or mint() — pass the Channel from use_channel()"
            )
    if not _cap_token(raw):
        raise RuntimeError(
            f"control_attrs failed to mint a Cap for {action!r}. "
            "Channel is live — refusing empty Cap (Cap Host would toast missing capability)."
        )
    raw.setdefault("data-ux-action", str(action))
    raw.setdefault("data-channel-action", str(action))
    for k, v in args.items():
        raw.setdefault(f"data-ux-arg-{k}", str(v))
    return raw


def mint_cap(
    channel: Any,
    action: str,
    args: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
) -> str:
    """Mint a real Channel Cap for *action*. Isolation door.

    Keyword args pass through to Channel.mint (``once=``, ``sub=``, …).
    Default is ``once=False`` (reusable). ``once=True`` is single-use at
    the Cap Host — compose does not own the once store.
    """
    if channel is None:
        raise RuntimeError(
            "mint_cap requires a live Channel. Call App.use_channel() first "
            "(Level 2). Offline Level 1 has no Caps to mint."
        )
    mint = getattr(channel, "mint", None)
    if not callable(mint):
        raise TypeError("channel has no mint() — pass the Channel from use_channel()")
    return mint(action, dict(args or {}), **kwargs)


_HTML_OPS = frozenset({"morph", "swap"})


def _wire_html(html: Any, sink: str) -> str:
    """HTML for the client, under the HTML sink contract (``html_text``)."""
    return str(html_text(html, sink=sink))


def _wire_plan(node: Any) -> Any:
    """Copy of a motion plan whose ``html`` fields follow the contract."""
    if isinstance(node, Mapping):
        out = {key: _wire_plan(value) for key, value in node.items()}
        if node.get("html") is not None:
            out["html"] = _wire_html(node["html"], "motion enter html")
        return out
    if isinstance(node, (list, tuple)):
        return [_wire_plan(item) for item in node]
    return node


def _wire_dict(op: Mapping) -> dict:
    out = dict(op)
    if out.get("op") in _HTML_OPS and "html" in out:
        out["html"] = _wire_html(out["html"], f"{out['op']} op html")
    if "plan" in out:
        out["plan"] = _wire_plan(out["plan"])
    return out


def ops_to_wire(ops: Any) -> list[dict]:
    """Project Behavior Op objects to Channel wire-shape dicts.

    Every HTML field the client inserts (morph / swap ``html``, motion
    ``enter`` ``html``) follows the HTML sink contract
    (``ux_compose.dom.html_text``): ``str`` / ``bytes`` → ux-dom
    ``sanitize_html``; ``__html__`` / a ux-dom tree → as written; any other
    type → ``TypeError``.
    """
    out: list[dict] = []
    if not ops:
        return out
    seq = ops if isinstance(ops, (list, tuple)) else [ops]
    for o in seq:
        if o is None:
            continue
        if isinstance(o, dict) and "op" in o:
            out.append(_wire_dict(o))
            continue
        ns = str(getattr(o, "ns", "") or "")
        name = str(getattr(o, "name", "") or "")
        payload = dict(getattr(o, "payload", None) or {})
        fq = f"{ns}.{name}" if ns else name
        if name == "morph" or fq.endswith(".morph"):
            html = payload.get("patch") if payload.get("patch") is not None else payload.get("html", "")
            target = str(payload.get("target") or "")
            if target and not target.startswith(("#", "[")):
                target = f"#{target}"
            out.append({"op": "morph", "target": target, "html": _wire_html(html, "morph html")})
        elif name in ("append", "notify", "toast") or ns in ("log", "notify"):
            out.append(
                {
                    "op": "toast",
                    "message": str(payload.get("message", "")),
                    "level": str(payload.get("level", "info")),
                }
            )
        elif name == "play" or ns == "transition":
            out.append({"op": "transition.play", "plan": _wire_plan(payload.get("plan", payload))})
        else:
            d = {"op": fq or "custom"}
            d.update(payload)
            out.append(_wire_dict(d))
    return out


def submit_intent(
    channel: Any,
    action: str,
    *,
    cap: Optional[str] = None,
    mint: bool = False,
    args: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
) -> Any:
    """Dispatch an Intent on Channel.registry.

    *mint=True* mints a real Cap first (Host path). Pass ``once=True``
    through to mint when the Cap should be single-use (default ``once=False``).
    *cap=* supplies an already-minted token.
    Missing Cap with require_cap=True → Result.ok is False (Cap Law).
    """
    if channel is None:
        raise RuntimeError(
            "submit_intent requires a live Channel. Call App.use_channel() first."
        )
    from ux_channel.protocol.types import Intent  # Isolation: only wire/

    payload = dict(args or {})
    token = cap
    mint_kw = {
        k: kwargs.pop(k)
        for k in ("once", "jti", "sub", "scopes", "extra")
        if k in kwargs
    }
    if token is None and mint:
        token = mint_cap(channel, action, payload, **mint_kw)
    intent = Intent(action=action, args=payload, cap=token)
    registry = getattr(channel, "registry", None)
    if registry is None or not hasattr(registry, "dispatch"):
        raise TypeError("channel has no registry.dispatch")
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return registry.dispatch(intent)
    raise RuntimeError(
        "submit_intent() called from a running event loop; "
        "use await async_submit_intent(...) instead"
    )


async def async_submit_intent(
    channel: Any,
    action: str,
    *,
    cap: Optional[str] = None,
    mint: bool = False,
    args: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
) -> Any:
    """Async Intent dispatch for ASGI handlers."""
    if channel is None:
        raise RuntimeError(
            "submit_intent requires a live Channel. Call App.use_channel() first."
        )
    from ux_channel.protocol.types import Intent  # Isolation: only wire/

    payload = dict(args or {})
    token = cap
    mint_kw = {
        k: kwargs.pop(k)
        for k in ("once", "jti", "sub", "scopes", "extra")
        if k in kwargs
    }
    if token is None and mint:
        token = mint_cap(channel, action, payload, **mint_kw)
    intent = Intent(action=action, args=payload, cap=token)
    registry = getattr(channel, "registry", None)
    if registry is None:
        raise TypeError("channel has no registry")
    adisp = getattr(registry, "async_dispatch", None)
    if not callable(adisp):
        return registry.dispatch(intent)
    return await adisp(intent)


def bridge_actions(behavior: Any, channel: Any) -> list[str]:
    """Register product @action names on Channel so Caps mint against author names.

    Channel verifies the Cap at the edge. The handler then calls
    ``dispatch_verified(name, payload)``. Trust is that one call. A task
    started while the action runs does not inherit it. A bool does not
    grant trust. Attaching Channel does not skip the check by itself
    (ux-behavior >=0.4.0).
    """
    registered: list[str] = []
    if behavior is None or channel is None:
        return registered
    registry = getattr(channel, "registry", None)
    if registry is None:
        return registered
    try:
        names = list(behavior.actions())
    except Exception:
        names = []
    for name in names:
        get = getattr(registry, "get", None)
        if callable(get) and get(name) is not None:
            continue

        def _handler(
            ctx: Any = None,
            *,
            _action: str = name,
            args: Any = None,
            principal: Any = None,  # the visitor; Channel injects it, not caller data
            **kw: Any,
        ) -> list[dict]:
            # Channel Intent is args=dict. dispatch_verified takes that payload.
            payload: dict[str, Any] = {}
            if isinstance(args, dict):
                payload.update(args)
            payload.update(kw)
            if ctx is not None:
                extra = getattr(ctx, "args", None)
                if isinstance(extra, dict):
                    for key, value in extra.items():
                        payload.setdefault(key, value)
            raw = behavior.dispatch_verified(_action, payload)
            return ops_to_wire(raw)

        try:
            channel.register(name, _handler)
            registered.append(name)
        except Exception:
            try:
                registry.register(name, _handler)
                registered.append(name)
            except Exception:
                pass
    return registered


__all__ = [
    "register_live_channel",
    "live_channel",
    "control_attrs",
    "mint_cap",
    "submit_intent",
    "async_submit_intent",
    "bridge_actions",
    "ops_to_wire",
]
