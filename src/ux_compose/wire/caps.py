"""Live Cap mint + Intent submit.

Isolation door only — product code never imports ux_channel. Authors reach
this through App.mint_cap / App.submit_intent (thin wrap) or this module.

Cap Law: Channel verifies the Cap at the edge; Behavior.dispatch after attach
is Host-internal (specialist contract — do not change Behavior).
"""

from __future__ import annotations

import asyncio
from typing import Any, Mapping, Optional


def mint_cap(
    channel: Any,
    action: str,
    args: Optional[Mapping[str, Any]] = None,
    **kwargs: Any,
) -> str:
    """Mint a real Channel Cap for *action*. Isolation door."""
    if channel is None:
        raise RuntimeError(
            "mint_cap requires a live Channel. Call App.use_channel() first "
            "(Level 2). Offline Level 1 has no Caps to mint."
        )
    mint = getattr(channel, "mint", None)
    if not callable(mint):
        raise TypeError("channel has no mint() — pass the Channel from use_channel()")
    return mint(action, dict(args or {}), **kwargs)


def ops_to_wire(ops: Any) -> list[dict]:
    """Project Behavior Op objects to Channel wire-shape dicts."""
    out: list[dict] = []
    if not ops:
        return out
    seq = ops if isinstance(ops, (list, tuple)) else [ops]
    for o in seq:
        if o is None:
            continue
        if isinstance(o, dict) and "op" in o:
            out.append(dict(o))
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
            out.append({"op": "morph", "target": target, "html": str(html or "")})
        elif name in ("append", "notify", "toast") or ns in ("log", "notify"):
            out.append(
                {
                    "op": "toast",
                    "message": str(payload.get("message", "")),
                    "level": str(payload.get("level", "info")),
                }
            )
        elif name == "play" or ns == "transition":
            out.append({"op": "transition.play", "plan": payload.get("plan", payload)})
        else:
            d = {"op": fq or "custom"}
            d.update(payload)
            out.append(d)
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

    *mint=True* mints a real Cap first (Host path).
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
    if token is None and mint:
        token = mint_cap(channel, action, payload)
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
    if token is None and mint:
        token = mint_cap(channel, action, payload)
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

    Channel verifies Caps at the edge; the handler then Host-dispatches with
    _trusted=True (Behavior._require_caps skips when _wire is set).
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
            **kw: Any,
        ) -> list[dict]:
            # Channel Intent is args=dict. Behavior.dispatch is **kwargs.
            payload: dict[str, Any] = {}
            if isinstance(args, dict):
                payload.update(args)
            payload.update(kw)
            if ctx is not None:
                extra = getattr(ctx, "args", None)
                if isinstance(extra, dict):
                    for key, value in extra.items():
                        payload.setdefault(key, value)
            raw = behavior.dispatch(_action, _trusted=True, **payload)
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
    "mint_cap",
    "submit_intent",
    "async_submit_intent",
    "bridge_actions",
    "ops_to_wire",
]
