"""DX probe — specialist detection for doctor and authoring tools.

Compose CLI is the sole product lifecycle (create-app / serve / deploy / doctor).
This package owns detection only — never re-implements DirectoryRoutes,
Tailwind, or specialist generators.
"""

from __future__ import annotations

from ux_compose.dx.probe import ProbeResult, probe

__all__ = ["ProbeResult", "probe"]
