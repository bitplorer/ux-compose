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
            "ux-channel is not installed. Level 2 (live Caps) requires: "
            "pip install ux-channel"
        ) from e

    behavior = getattr(app, "_behavior", None)
    if behavior is None and hasattr(app, "use_behavior"):
        app.use_behavior()
        behavior = getattr(app, "_behavior", None)

    # Already a Channel instance — bind only, never boot/attach as asgi
    if channel is not None and _is_channel(channel):
        _bind_wire(behavior, channel)
        _bridge(behavior, channel)
        return channel

    asgi = asgi_app if _is_asgi_app(asgi_app) else None
    if asgi is not None and _is_channel(asgi):
        asgi = None  # refuse Channel-as-asgi

    cfg = config
    if cfg is None and secret is not None:
        try:
            cfg = ChannelConfig(secret=secret)
        except Exception:
            cfg = None

    # Preferred path: Behavior.attach owns Channel.boot on real ASGI
    if behavior is not None and hasattr(behavior, "attach") and asgi is not None:
        attach_kwargs: dict[str, Any] = {}
        if secret is not None:
            attach_kwargs["secret"] = secret
        try:
            behavior.attach(asgi, **attach_kwargs)
            ch = getattr(behavior, "_wire", None)
            _bridge(behavior, ch)
            return ch
        except TypeError:
            # Older attach() signatures — retry positional
            try:
                behavior.attach(asgi)
                ch = getattr(behavior, "_wire", None)
                _bridge(behavior, ch)
                return ch
            except Exception:
                if asgi is not None:
                    raise
        except Exception:
            raise

    # Headless / fallback boot
    try:
        if cfg is not None:
            ch = Channel.boot(config=cfg)
        else:
            ch = Channel.boot()
    except Exception:
        ch = None
    _bind_wire(behavior, ch)
    _bridge(behavior, ch)
    return ch


def _as_runtime(obj: Any) -> Any:
    """Document.use wants instances (XElement(), Csp.auto(), Motion()).

    Passing the class makes ``document.mount`` call ``served_files()``
    unbound (``missing self``).
    """
    if obj is None:
        return None
    if isinstance(obj, type):
        try:
            return obj()
        except TypeError:
            return obj
    return obj


def attach_motion(document: Any = None) -> tuple[Any, Any]:
    """
    Return (Motion, MotionChannel) **instances** for Document.use(...).
    Raises ImportError if ux-motion is absent.
    """
    try:
        from ux_motion import Motion, MotionChannel  # Isolation: only here
    except ImportError as e:
        raise ImportError(
            "ux-motion is not installed. Level 3 requires: pip install ux-motion"
        ) from e
    motion = _as_runtime(Motion)
    channel = _as_runtime(MotionChannel)
    if document is not None and hasattr(document, "use"):
        document.use(motion, channel)
    return motion, channel


def attach_document_runtimes(
    document: Any,
    *,
    motion: bool = False,
    channel_scripts: bool = False,
    htmx: bool = False,
) -> Any:
    """
    Attach progressive runtimes to a Document. Controlled door only.

    Default control plane is stack-native (XElement + Csp). HTMX is **opt-in**
    via ``htmx=True`` — never a hard dependency of compose.
    """
    try:
        from ux_dom.runtime import XElement, Csp  # type: ignore
    except ImportError:
        # Dom not installed — caller handles
        return document

    runtimes: list[Any] = [XElement(), Csp.auto()]
    if htmx:
        try:
            from ux_dom.runtime import Htmx  # type: ignore

            runtimes.insert(1, Htmx())
        except ImportError:
            pass
    if motion:
        motion_rt, channel_rt = attach_motion()
        runtimes.extend([motion_rt, channel_rt])
    # Channel scripts are typically attached via Channel.boot / Document.use
    if document is not None and hasattr(document, "use"):
        document.use(*runtimes)
    return document


__all__ = ["attach_channel", "attach_motion", "attach_document_runtimes"]
