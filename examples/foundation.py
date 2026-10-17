"""Foundation — Counter, Toggle, MorphState vs RefState.

Read this file first. Every later example is this shape:

    class Thing(Component):
        id = "stable-css-id"          # morph target
        visible = MorphState(...)     # mutation ⇒ this unit must morph
        memory = RefState(...)        # silent; does not dirty alone
        def render(self): ...         # returns a ux-dom tag tree
        @action(caps=()) def verb(...): mutate; return update_with(self, plan)

Return algebra (hard contract):
  1. return None            → auto-morph dirty MorphState units
  2. return list[Op]        → exact Ops; auto-morph suppressed
  3. Prefer update_with(self, plan, extra_ops=[notify(...)])
     Morph HTML is live render(); Plan has no html= (XOR).

Progressive Superpower: this file is valid at L1 (offline dispatch) and at
L3 (Channel + Motion) without rewriting the class.

Run:
  PYTHONPATH=src:. python examples/foundation.py
"""
from __future__ import annotations

from ux_compose import (
    App,
    doctor,
)

from ux_compose.components.counter import Counter
from ux_compose.components.planes import Planes
from ux_compose.components.toggle import Toggle


def demo() -> None:
    app = App.boot("Foundation")
    app.add(Counter, Toggle, Planes)
    print("Level:", int(app.level), app.level.label)
    print("inc", app.dispatch("counter.inc", sku="tick"))
    print("flip", app.dispatch("toggle.flip"))
    print("morph", app.dispatch("planes.morph_only"))
    strict = App.boot("Foundation", strict_caps=True)
    strict.add(Counter)
    try:
        strict.dispatch("counter.reset")
        print("UNEXPECTED reset")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__, "— reset refused offline under strict_caps")
    report = doctor([], fail=False)
    print("Doctor ok:", report.ok, "L" + str(report.level_available))


if __name__ == "__main__":
    demo()
