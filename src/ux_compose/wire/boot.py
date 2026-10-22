"""
wire/ is the package door that may import ux_channel, MotionChannel, or CEK.
This module is one of three files in that door (boot.py, caps.py, cek.py).

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

import hashlib
import hmac
from typing import Any

from ux_compose import visitor


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


def visitor_key(channel: Any) -> bytes:
    """Visitor-cookie signing key, derived from the Channel secret.

    A separate purpose key: a visitor cookie can never pass as a Cap.
    """
    secret = str(channel.config.secret).encode("utf-8")
    return hmac.new(secret, b"ux-compose/visitor/v1", hashlib.sha256).digest()


def _bind_visitors(channel: Any, asgi: Any) -> None:
    """Caps run only for the visitor they were minted for.

    The Channel principal is the request's subject (``visitor.resolve``):
    the logged-in user, else the signed anonymous visitor. On a real ASGI
    app, ``VisitorMiddleware`` binds the same subject for page renders and
    mints the visitor cookie.
    """
    from ux_channel import Principal  # Isolation: only here

    key = visitor_key(channel)

    def principal(request: Any) -> Any:
        subject = visitor.resolve(key, getattr(request, "scope", None) or {})
        return Principal(id=subject) if subject else None

    channel.registry.auth_resolver = principal
    if asgi is not None:
        asgi.add_middleware(visitor.VisitorMiddleware, key=key)


def attach_channel(
    app: Any,
    *,
    channel: Any = None,
    config: Any = None,
    asgi_app: Any = None,
    secret: str | None = None,
) -> Any:
    """
    Attach Channel to the App / Behavior. Called only from App.use_channel().

    Isolation-safe host adapter:
      - If *asgi_app* is FastAPI/Starlette, Behavior.attach(asgi) owns
        Channel.boot so include_router lands on the real ASGI app.
      - If *channel* is already a Channel, bind it as _wire — never
        Channel.boot(channel) / Behavior.attach(channel).
      - Headless (no ASGI): Channel.boot(config=) for mint/submit tests.
        ChannelConfig(secret=) and Channel.boot fail closed (no silent
        cfg=None / ch=None).
      - Compose door is Channel.boot (not ActionRegistry.from_config —
        that name is not a frozen wire import). Boot applies the same
        Cap adapter as from_config when cek != off. Do not assume
        classic CapService after boot with cek=require.

    Returns the Channel instance (or None if ux-channel is used later by the host).
    Raises ImportError with a clear progressive message if ux-channel is absent.
    """
    try:
        from ux_channel import Channel, ChannelConfig  # Isolation: only here
    except ImportError as e:
        raise ImportError(
            "ux-channel is required (Python ≥3.14). "
            "ux-compose hard-depends on the pinned specialist stack. "
            "Isolation: attach only through App.use_channel (wire/)."
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
        cfg = ChannelConfig(secret=secret)

    # Preferred path: Behavior.attach owns Channel.boot on real ASGI
    if behavior is not None and hasattr(behavior, "attach") and asgi is not None:
        attach_kwargs: dict[str, Any] = {}
        if secret is not None:
            attach_kwargs["secret"] = secret
        # Any attach failure must raise: a short secret, a REDIS_URL
        # Channel.boot refuses, anything else. The default leaves the
        # process up with no Caps.
        behavior.strict_attach = True
        behavior.attach(asgi, **attach_kwargs)
        ch = getattr(behavior, "_wire", None)
        _bridge(behavior, ch)
        if ch is not None:
            _bind_visitors(ch, asgi)
        return ch

    # Headless / fallback boot — fail closed (do not impersonate offline)
    if cfg is not None:
        ch = Channel.boot(config=cfg)
    else:
        ch = Channel.boot()
    _bind_wire(behavior, ch)
    _bridge(behavior, ch)
    _bind_visitors(ch, None)
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
            "ux-motion is required (Python ≥3.14). "
            "ux-compose hard-depends on the pinned specialist stack."
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
    htmx: bool = False,
) -> Any:
    """
    Attach progressive runtimes to a Document. Controlled door only.

    Default control plane is stack-native (XElement + Csp). HTMX is **opt-in**
    via ``htmx=True`` — never a hard dependency of compose.
    """
    try:
        from ux_dom import XElement, Csp  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "ux-dom is required (Python ≥3.14). "
            "ux-compose hard-depends on the pinned specialist stack."
        ) from exc

    runtimes: list[Any] = [XElement(), Csp.auto()]
    if htmx:
        from ux_compose.htmx import Htmx

        runtimes.insert(1, Htmx())
    if motion:
        motion_rt, channel_rt = attach_motion()
        runtimes.extend([motion_rt, channel_rt])
    # Channel scripts are typically attached via Channel.boot / Document.use
    if document is not None and hasattr(document, "use"):
        document.use(*runtimes)
    return document


__all__ = ["attach_channel", "attach_motion", "attach_document_runtimes"]
