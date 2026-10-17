"""Settings — Density and motion are names. Wipe is authority (admin.reset lineage).

Ported from the ``ops`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    App,
    Component,
    MorphState,
    RefState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    header,
    ul,
    li,
    span,
    section,
)

from ux_compose.author import act, mark_dirty, status

class Settings(Component):
    """Density and motion are names. Wipe is authority (admin.reset lineage)."""

    id = "settings"
    density = MorphState("roomy")
    motion = MorphState("allow")
    dirty = MorphState("idle")

    def render(self):
        dens = str(self.density or "roomy")
        mot = str(self.motion or "allow")
        kids = (
            header(
                p("Named prefs · wipe is a Cap", className="kicker"),
                h2("Settings", className="widget-title"),
            ),
            p("Paper house stays light-only. Density and motion still switch.", className="lede"),
            p("Density", className="kicker"),
            div(
                act("settings.set_density", "Roomy", kind="primary" if dens == "roomy" else "ghost", key="roomy"),
                act("settings.set_density", "Compact", kind="primary" if dens == "compact" else "ghost", key="compact"),
                className="seg",
            ),
            p("Motion", className="kicker"),
            div(
                act("settings.set_motion", "Allow", kind="primary" if mot == "allow" else "ghost", key="allow"),
                act("settings.set_motion", "Reduce", kind="primary" if mot == "reduce" else "ghost", key="reduce"),
                className="seg",
            ),
            act("settings.wipe", "Wipe local prefs (Cap)", kind="text"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def set_density(self, key: str = "roomy"):
        self.density = key if key in {"roomy", "compact"} else "roomy"
        return update_with(self)

    @action(caps=())
    def set_motion(self, key: str = "allow"):
        self.motion = key if key in {"allow", "reduce"} else "allow"
        return update_with(self)

    @action(caps=("admin.reset",))
    def wipe(self):
        self.density = "roomy"
        self.motion = "allow"
        mark_dirty(self)
        return update_with(self, extra_ops=[notify("wiped")])


__all__ = ["Settings"]
