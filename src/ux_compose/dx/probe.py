"""Probe specialist packages and their CLI entrypoints.

Pure, side-effect free, offline-safe. Used by doctor (and authors who want
the same matrix). Never starts a server and never shells out to another CLI.
"""

from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, field
from typing import Optional


# (import name, preferred CLI binary on PATH, human label)
_SPECIALISTS = (
    ("ux_dom", "uxdom", "ux-dom"),
    ("ux_behavior", "uxbehavior", "ux-behavior"),
    ("ux_motion", None, "ux-motion"),
    ("ux_channel", "uxchannel", "ux-channel"),
)


@dataclass(frozen=True)
class ProbeResult:
    """Snapshot of which progressive specialists are available right now."""

    specialists: dict[str, bool] = field(default_factory=dict)
    """import-name → True if find_spec succeeds."""

    clis: dict[str, Optional[str]] = field(default_factory=dict)
    """CLI binary name → absolute path if on PATH, else None."""

    labels: dict[str, str] = field(default_factory=dict)
    """import-name → human package label (ux-dom, …)."""

    @property
    def level_available(self) -> int:
        """Highest progressive level supported by installed packages.

        L0 always available (static). L1 needs behavior, L2 channel, L3 motion.
        """
        s = self.specialists
        level = 0
        if s.get("ux_behavior"):
            level = 1
        if s.get("ux_channel"):
            level = 2
        if s.get("ux_motion"):
            level = 3
        return level

    @property
    def has_dom(self) -> bool:
        return bool(self.specialists.get("ux_dom"))

    @property
    def has_dom_cli(self) -> bool:
        path = self.clis.get("uxdom")
        return bool(path)

    @property
    def has_behavior(self) -> bool:
        return bool(self.specialists.get("ux_behavior"))

    @property
    def has_channel(self) -> bool:
        return bool(self.specialists.get("ux_channel"))

    @property
    def has_motion(self) -> bool:
        return bool(self.specialists.get("ux_motion"))

    def unlock_messages(self, *, requested_level: int = 3) -> list[str]:
        """Teaching lines for the next unlock(s) relative to installed packages."""
        lines: list[str] = []
        s = self.specialists
        if requested_level >= 1 and not s.get("ux_behavior"):
            lines.append(
                "L1 offline interactive: pip install ux-behavior  →  App.boot(...).use_behavior()"
            )
        if requested_level >= 2 and not s.get("ux_channel"):
            lines.append(
                "L2 live Caps: pip install ux-channel  →  app.use_channel(asgi_app=...)"
            )
        if requested_level >= 3 and not s.get("ux_motion"):
            lines.append(
                "L3 choreography: pip install ux-motion  →  app.use_motion()"
            )
        if not lines:
            lines.append(
                f"Specialists present for L{self.level_available}. "
                "Progressive Superpower: Level-1 code stays correct at higher levels."
            )
        return lines

    def summary_lines(self) -> list[str]:
        """Human-readable capability matrix for doctor / CLI output."""
        out = []
        for import_name, cli_name, label in _SPECIALISTS:
            present = self.specialists.get(import_name, False)
            mark = "✓" if present else "·"
            extra = ""
            if cli_name:
                path = self.clis.get(cli_name)
                extra = f"  cli={path}" if path else "  cli=—"
            out.append(f"  {mark} {label}{extra}")
        out.append(f"  Progressive level available: L{self.level_available}")
        return out


def probe() -> ProbeResult:
    """Detect installed specialists and CLI binaries. Never raises."""
    specialists: dict[str, bool] = {}
    clis: dict[str, Optional[str]] = {}
    labels: dict[str, str] = {}

    for import_name, cli_name, label in _SPECIALISTS:
        labels[import_name] = label
        try:
            specialists[import_name] = importlib.util.find_spec(import_name) is not None
        except (ModuleNotFoundError, ValueError, AttributeError):
            specialists[import_name] = False
        if cli_name:
            clis[cli_name] = shutil.which(cli_name)

    return ProbeResult(specialists=specialists, clis=clis, labels=labels)


__all__ = ["ProbeResult", "probe"]
