"""MotionBox — MotionBox

Ported from the ``motion_xor`` example module (spec §4); this module is canonical and the example imports it.
"""
from __future__ import annotations

from ux_compose import (
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
    span,
)

from ux_compose.author import act, optional_plan
from ux_compose import scene, fade

class MotionBox(Component):
    id = "motionbox"
    pose = MorphState("rest")
    hops = RefState(0)

    def render(self):
        pose = str(self.pose or "rest")
        kids = (
            header(
                p("Morph then play", className="kicker"),
                h2("Motion box", className="widget-title"),
            ),
            p(
                span(pose, className="chip"),
                span(f"hops {int(self.hops or 0)}", className="muted"),
                className="chip-row",
            ),
            div(
                span("rest" if pose == "rest" else "in air", id="motionbox-face", className="motion-face"),
            ),
            p(
                "Plan has no html=. Patch is render(). Motion plays #motionbox-face "
                "after the morph — XOR, Morph-then-Play.",
                className="lede",
            ),
            div(
                act("motionbox.hop", "Hop (XOR-safe)", kind="primary"),
                act("motionbox.rest", "Rest", kind="ghost"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget", data_pose=pose)

    @action(caps=())
    def hop(self):
        self.pose = "air"
        self.hops = int(self.hops or 0) + 1
        plan = optional_plan("box-hop", "#motionbox-face", ms=220)
        return update_with(self, plan, extra_ops=[notify("hop")])

    @action(caps=())
    def rest(self):
        self.pose = "rest"
        plan = scene("box-rest").enter("#motionbox-face", fade.enter(ms=140))
        return update_with(self, plan)


__all__ = ["MotionBox"]
