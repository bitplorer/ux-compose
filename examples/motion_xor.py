"""Motion + XOR + Morph-then-Play.

Laws:
  XOR            morph(target) XOR scene.enter(target, html=...)
  Morph-then-Play  morph Op is first; transition.play follows
  Isolation      Plan comes from ux_compose.scene (re-export), never ux_channel

Do:
    return update_with(self, scene("pop").enter("#box", rise.enter(ms=140)))

Don't:
    return scene("pop").enter("#box", rise.enter(ms=140), html=self.render())

The helper serializes live render() into the morph patch. The Plan carries
recipes only. Without ux-motion, ``scene`` is None and the same action still
morphs — Progressive Superpower.

Run:
  PYTHONPATH=src:. python examples/motion_xor.py
"""
from __future__ import annotations

from ux_compose import (
    HAS_DOM,
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
    span,
)

from examples._common import act, tick, maybe_plan, scene, rise, fade


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
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_pose=pose)
        return f'<div id="{self.id}">{pose}</div>'

    @action(caps=())
    def hop(self):
        self.pose = "air"
        self.hops = int(self.hops or 0) + 1
        plan = maybe_plan("box-hop", "#motionbox-face", ms=220)
        return update_with(self, plan, extra_ops=[notify("hop")])

    @action(caps=())
    def rest(self):
        self.pose = "rest"
        plan = None
        if scene is not None and fade is not None:
            try:
                plan = scene("box-rest").enter("#motionbox-face", fade.enter(ms=140))
            except Exception:
                plan = None
        return update_with(self, plan)


class ShareSeat(Component):
    """Shared-element seat: leave #from-sku, arrive #to-sku, same share id."""

    id = "share"
    place = MorphState("shelf")
    sku = RefState("linen")

    def render(self):
        on_shelf = self.place != "bag"
        kids = (
            header(
                p("scene.share continuity id", className="kicker"),
                h2("Shared element", className="widget-title"),
            ),
            div(
                span("Shelf", id="from-linen", className="chip" + (" is-on" if on_shelf else "")),
                span("Bag", id="to-linen", className="chip" + ("" if on_shelf else " is-on")),
                className="chip-row",
            ),
            act(
                "share.fly",
                "Shelf → bag" if on_shelf else "Bag → shelf",
                kind="primary",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{self.place}</div>'

    @action(caps=())
    def fly(self):
        going_to_bag = self.place != "bag"
        self.place = "bag" if going_to_bag else "shelf"
        plan = None
        if scene is not None and rise is not None:
            try:
                leave, arrive = (
                    ("#from-linen", "#to-linen") if going_to_bag else ("#to-linen", "#from-linen")
                )
                plan = (
                    scene("line-to-bag")
                    .share("sku-linen", leave=leave, arrive=arrive, recipe=rise.enter(ms=120))
                    .enter(f"#{self.id}", rise.enter(ms=140))
                )
            except Exception:
                plan = None
        return update_with(self, plan, extra_ops=[notify(self.place)])


def demo() -> None:
    app = App.boot("Motion", strict_caps=False)
    app.add(MotionBox, ShareSeat)
    print("motion available", scene is not None)
    print("hop", app.dispatch("motionbox.hop"))
    print("share", app.dispatch("share.fly"))


if __name__ == "__main__":
    demo()
