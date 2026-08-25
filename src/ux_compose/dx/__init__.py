"""DX probe — specialist detection for doctor and authoring tools.

Compose CLI is the sole product lifecycle (create-app / build / serve / deploy / doctor).
This *module* only probes what is installed. Tailwind compiler lives in
``ux_compose.tailwind``. DirectoryRoutes lives in ``ux_compose.routing``.
"""

from __future__ import annotations

from ux_compose.dx.probe import ProbeResult, probe

__all__ = ["ProbeResult", "probe"]
