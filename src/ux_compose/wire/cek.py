"""Optional CEK door — Isolation-safe, progressive, degrade if cek_host absent.

Product code never imports cek_host / cek_surface. Authors reach this only
through App.use_cek() or this module (wire/).
"""

from __future__ import annotations

from typing import Any, Optional


def attach_cek(channel: Any, *, mode: str = "adapt") -> Optional[str]:
    """Attach CEK Cap adapter to a live Channel.

    mode:
      off     — no-op
      adapt   — Host adapter live; Channel CapService remains authority
      require — CapService replaced by cek_host.Host (hard fail if missing)

    Returns the resolved mode string, or None when the specialist is absent
    and mode is not require (progressive degrade).
    """
    resolved = (mode or "off").strip().lower()
    if resolved in ("", "off", "0", "false", "no"):
        return "off"
    if resolved not in ("adapt", "require"):
        resolved = "adapt"

    if channel is None:
        if resolved == "require":
            raise RuntimeError("use_cek(require) needs a live Channel (App.use_channel first)")
        return None

    try:
        from ux_channel.cek.host_adapter import apply_host_adapter  # Isolation: only here
    except ImportError:
        if resolved == "require":
            raise ImportError(
                "CEK require mode needs ux-channel with the CEK adapter. "
                "Stay at Channel Caps (mode='off' or omit use_cek)."
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
