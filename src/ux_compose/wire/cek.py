"""Optional CEK door — Isolation-safe, progressive, degrade if cek_host absent.

Attaches the **Cap Host** (cek-runtime via Channel façade). That noun is
not the HTTP Product host (Clock A / compose ADR 0002).

Product code never imports cek_host / cek_surface. Authors reach this only
through App.use_cek() or this module (wire/).
"""

from __future__ import annotations

from typing import Any, Optional

_OFF_ALIASES = ("off", "0", "false", "no")
_OFF_REFUSE = (
    'use_cek(off) cannot leave Cap Host live (CekHostCapService / '
    'kernel_ssot="cek-runtime"). Boot ChannelConfig(cek="off") instead.'
)


def _cap_host_is_live(channel: Any) -> bool:
    if channel is None:
        return False
    caps = getattr(getattr(channel, "registry", None), "_caps", None)
    if caps is None:
        return False
    if type(caps).__name__ == "CekHostCapService":
        return True
    return getattr(caps, "kernel_ssot", None) == "cek-runtime"


def attach_cek(channel: Any, *, mode: str = "require") -> Optional[str]:
    """Attach CEK Cap Host adapter to a live Channel.

    Cap Host (cek-runtime via Channel) ≠ HTTP Product host (Clock A).

    mode:
      off     — not a silent no-op after require. Refuses if Cap Host is
                already live; boot ChannelConfig(cek="off") instead.
                Does not restore via apply_host_adapter (that path is not
                a restore). Honest no-op only when classic CapService is
                already on registry._caps.
      adapt   — compare-only lab; Channel CapService remains authority
      require — product Cap Host (cek-runtime via Channel). Default.
                Unknown values resolve to require.

    Returns the resolved mode string, or None when the specialist is absent
    and mode is not require (progressive degrade).
    """
    resolved = (mode or "require").strip().lower()
    if resolved in _OFF_ALIASES:
        if _cap_host_is_live(channel):
            raise RuntimeError(_OFF_REFUSE)
        return "off"
    if resolved not in ("adapt", "require"):
        resolved = "require"

    if channel is None:
        if resolved == "require":
            raise RuntimeError("use_cek(require) needs a live Channel (App.use_channel first)")
        return None

    try:
        from ux_channel.cek.host_adapter import apply_host_adapter  # Isolation: wire/ only
    except ImportError:
        if resolved == "require":
            raise ImportError(
                "CEK require mode needs ux-channel with the CEK adapter. "
                "Stay at Channel Caps (mode='off')."
            )
        return None

    try:
        import cek_host  # noqa: F401
    except ImportError:
        if resolved == "require":
            raise ImportError(
                "CEK require mode needs cek_host. "
                "pip install 'cek-host>=0.1.3'. Channel Caps continue to work without it."
            )
        return None

    cfg = getattr(channel, "config", None)
    if cfg is not None:
        # ChannelConfig is frozen; setattr is a no-op. replace() so the
        # author's mode reaches apply_host_adapter (Cap decide stays there).
        try:
            from dataclasses import is_dataclass, replace

            if is_dataclass(cfg) and "cek" in getattr(cfg, "__dataclass_fields__", {}):
                cfg = replace(cfg, cek=resolved)
                try:
                    object.__setattr__(channel, "config", cfg)
                except Exception:
                    pass
            else:
                object.__setattr__(cfg, "cek", resolved)
        except Exception:
            try:
                setattr(cfg, "cek", resolved)
            except Exception:
                pass
    registry = getattr(channel, "registry", None)
    if registry is None:
        if resolved == "require":
            raise RuntimeError("Channel has no registry for CEK adapter")
        return None
    return apply_host_adapter(registry, cfg)


__all__ = ["attach_cek"]
