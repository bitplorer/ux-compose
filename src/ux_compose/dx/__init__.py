"""DX probe and progressive shim helpers for ux-compose.

Compose CLI is a progressive shim over specialist DX (ux-dom, ux-behavior,
ux-motion, ux-channel). This package owns detection only — never re-implements
DirectoryRouting, Tailwind, or specialist generators.
"""

from __future__ import annotations

from ux_compose.dx.probe import ProbeResult, probe

__all__ = ["ProbeResult", "probe"]
