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
    """Snapshot of whether the pinned specialist stack is present.

    Incomplete install is fail-loud. Levels 0–3 are attach APIs after
    the complete stack is present — not an optional-package unlock.
    """

    specialists: dict[str, bool] = field(default_factory=dict)
    """import-name → True if find_spec succeeds."""

    clis: dict[str, Optional[str]] = field(default_factory=dict)
    """CLI binary name → absolute path if on PATH, else None."""

    labels: dict[str, str] = field(default_factory=dict)
    """import-name → human package label (ux-dom, …)."""

    @property
    def level_available(self) -> int:
        """Highest attach level the present stack can support.

        Incomplete install is fail-loud via ``unlock_messages`` / doctor.
        L0–L3 are attach APIs on a complete install, not package unlocks.
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
        """Fail-loud diagnostics when the pinned stack is incomplete.

        Levels are additive attach APIs after a complete install — not
        an optional-package unlock ladder.
        """
        lines: list[str] = []
        s = self.specialists
        missing = []
        if not s.get("ux_behavior"):
            missing.append("ux-behavior")
        if not s.get("ux_channel"):
            missing.append("ux-channel")
        if not s.get("ux_motion"):
            missing.append("ux-motion")
        if not s.get("ux_dom"):
            missing.append("ux-dom")
        if missing:
            lines.append(
                "incomplete stack: missing "
                + ", ".join(missing)
                + ". Complete install first (Python ≥3.14). "
                "Levels are additive after the stack is present."
            )
        else:
            lines.append(
                f"Full stack present (L{self.level_available}). "
                "Progressive Superpower: complete install first; "
                "Level-1 code stays correct at higher levels."
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
