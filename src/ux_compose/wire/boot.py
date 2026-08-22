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
