"""
wire/boot.py — the ONLY place that may import ux_channel, MotionChannel, or CEK.

Isolation Law is enforced by package structure + doctor.
Product code and the public surface of ux_compose never import from here
except through the controlled App.use_channel / use_motion paths.

Attach order (Attach Order Law):
    Document.use(Motion, MotionChannel, ...); Channel.boot(asgi); Behavior.attach(asgi).

Behavior.attach(asgi) owns Channel.boot(asgi). Passing a Channel instance as
the asgi argument makes Channel.boot call include_router on Channel — that
is the include_router soft-fail. This module never does that.
"""

from __future__ import annotations

from typing import Any, Optional


def _is_asgi_app(obj: Any) -> bool:
    """True for FastAPI / Starlette (have include_router). Channel does not."""
    return obj is not None and hasattr(obj, "include_router")


def _is_channel(obj: Any) -> bool:
    return (
        obj is not None
        and type(obj).__name__ == "Channel"
        and hasattr(obj, "registry")
        and hasattr(obj, "mint")
    )


def _bind_wire(behavior: Any, channel: Any) -> None:
    """Set Behavior._wire without re-booting Channel (no include_router)."""
    if behavior is None or channel is None:
        return
    if getattr(behavior, "_wire", None) is None:
        behavior._wire = channel


def _bridge(behavior: Any, channel: Any) -> None:
    if behavior is None or channel is None:
        return
    try:
        from ux_compose.wire.caps import bridge_actions

        bridge_actions(behavior, channel)
    except Exception:
        pass


def attach_channel(
    app: Any,
    *,
    channel: Any = None,
    config: Any = None,
    asgi_app: Any = None,
    secret: str | None = None,
    **_ignored: Any,
) -> Any:
    """
    Attach Channel to the App / Behavior. Called only from App.use_channel().

    Isolation-safe host adapter:
      - If *asgi_app* is FastAPI/Starlette, Behavior.attach(asgi) owns
        Channel.boot so include_router lands on the real ASGI app.
      - If *channel* is already a Channel, bind it as _wire — never
        Channel.boot(channel) / Behavior.attach(channel).
      - Headless (no ASGI): Channel.boot(config=) for mint/submit tests.

    Returns the Channel instance (or None if ux-channel is used later by the host).
    Raises ImportError with a clear progressive message if ux-channel is absent.
    """
    try:
        from ux_channel import Channel, ChannelConfig  # Isolation: only here
    except ImportError as e:
        raise ImportError(
            "Level 2 (live Caps) requires ux-channel. "
            "Install with: pip install 'ux-compose[channel]'  or  pip install ux-channel. "
            "Level 1 offline continues to work without it."
        ) from e

    if config is None:
        secret = secret or ("dev-" + "x" * 32)
        config = ChannelConfig.development(secret=secret, allow_memory_stores=True)

    behavior = getattr(app, "_behavior", None)
    ch: Any = None

    # 1. Caller supplied a live Channel — bind, do not re-boot.
    if channel is not None:
        if _is_channel(channel):
            ch = channel
            _bind_wire(behavior, ch)
            _bridge(behavior, ch)
            return ch
        # Defensive: someone passed FastAPI as channel=
        if _is_asgi_app(channel) and asgi_app is None:
            asgi_app = channel

    # 2. FastAPI / Starlette — Behavior.attach owns Channel.boot(asgi).
    if asgi_app is not None:
        if _is_channel(asgi_app):
            # Recovery: never Channel.boot(Channel) — that is include_router fail.
            ch = asgi_app
            _bind_wire(behavior, ch)
            _bridge(behavior, ch)
            return ch
        if _is_asgi_app(asgi_app) and behavior is not None and hasattr(behavior, "attach"):
            secret_kw = secret or getattr(config, "secret", None)
            attached = behavior.attach(asgi_app, secret=secret_kw)
            if attached is not None:
                ch = attached
            else:
                # Soft attach failure — still boot on the real ASGI app.
                ch = Channel.boot(asgi_app, config=config)
                _bind_wire(behavior, ch)
            _bridge(behavior, ch)
            return ch
        # ASGI-like but no Behavior yet: boot on the app so routes still mount.
        ch = Channel.boot(asgi_app, config=config)
        _bind_wire(behavior, ch)
        _bridge(behavior, ch)
        return ch

    # 3. Headless Channel (tests, mint without HTTP). No include_router.
    ch = Channel.boot(config=config)
    _bind_wire(behavior, ch)
    _bridge(behavior, ch)
    return ch


def attach_motion(document: Any = None) -> tuple[Any, Any]:
    """
    Return (Motion, MotionChannel) runtimes for Document.use(...).
    Only called from controlled App.use_motion / boot paths.
    """
    try:
        from ux_motion import Motion, MotionChannel  # Isolation: only here
    except ImportError as e:
        raise ImportError(
            "Level 3 (choreographed motion) requires ux-motion. "
            "Install with: pip install 'ux-compose[motion]'  or  pip install ux-motion. "
            "Levels 0–2 continue to work without it."
        ) from e
    return Motion(), MotionChannel()


def attach_document_runtimes(
    document: Any,
    *,
    motion: bool = False,
    channel_scripts: bool = False,
) -> Any:
    """
    Attach progressive runtimes to a Document. Controlled door only.
    """
    try:
        from ux_dom.runtime import XElement, Htmx, Csp  # type: ignore
    except ImportError:
        # Dom not installed — caller handles
        return document

    runtimes = [XElement(), Htmx(), Csp.auto()]
    if motion:
        Motion, MotionChannel = attach_motion()
        runtimes.extend([Motion, MotionChannel])
    # Channel scripts are typically attached via Channel.boot / Document.use
    if document is not None and hasattr(document, "use"):
        document.use(*runtimes)
    return document


__all__ = ["attach_channel", "attach_motion", "attach_document_runtimes"]
