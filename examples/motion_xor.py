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
recipes only. ux-motion is a hard dependency; L1 dispatch still morphs
without attaching Motion (Progressive Superpower).

Run:
  PYTHONPATH=src:. python examples/motion_xor.py
"""
from __future__ import annotations

from ux_compose import (
    App,
)

from ux_compose.components.motionbox import MotionBox
from ux_compose.components.shareseat import ShareSeat


def demo() -> None:
    app = App.boot("Motion")
    app.add(MotionBox, ShareSeat)
    print("hop", app.dispatch("motionbox.hop"))
    print("share", app.dispatch("share.fly"))


if __name__ == "__main__":
    demo()
