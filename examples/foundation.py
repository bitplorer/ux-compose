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
    HAS_DOM,
    App,
    Component,
    MorphState,
    RefState,
    action,
    doctor,
    notify,
    update_with,
    div,
    h2,
    p,
    span,
    header,
)

from examples._common import act, maybe_plan, tick


class Counter(Component):
    """Increment is public. Reset is Cap-protected (Authority Clock).

    ``n`` is RefState because Channel's session plane refuses quantity
    MorphState values. ``stamp`` is the dirty tick so the unit still morphs.
    """

    id = "counter"
    n = RefState(0)
    last = RefState("")
    stamp = MorphState("idle")

    def render(self):
        n = int(self.n or 0)
        last = str(self.last or "—")
        body = (
            header(
                p("Magnitude lives in RefState", className="kicker"),
                h2("Counter", className="widget-title"),
                className="widget-head",
            ),
            p(
                span(str(n), className="num"),
                span(f"last {last}", className="muted"),
                className="counter-face",
            ),
            div(
                act("counter.dec", "Decrease", kind="ghost"),
                act("counter.inc", "Increase", kind="primary", sku="tick"),
                act("counter.reset", "Reset", kind="text"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*body, id=self.id, className="widget", data_stamp=str(self.stamp))
        return f'<div id="{self.id}" class="widget" data-n="{n}">n={n}</div>'

    @action(caps=())
    def inc(self, sku: str = ""):
        self.n = int(self.n or 0) + 1
        self.last = sku or "inc"
        tick(self)
        return update_with(
            self,
            maybe_plan("counter-inc", f"#{self.id}", ms=120),
            extra_ops=[notify(f"n={self.n}")],
        )

    @action(caps=())
    def dec(self):
        self.n = max(0, int(self.n or 0) - 1)
        self.last = "dec"
        tick(self)
        return update_with(self, extra_ops=[notify(f"n={self.n}")])

    @action(caps=("admin.reset",))
    def reset(self):
        """Fails closed offline under strict_caps; live path needs a minted Cap."""
        self.n = 0
        self.last = ""
        tick(self)
        return update_with(self, extra_ops=[notify("reset")])


class Toggle(Component):
    """Boolean MorphState is qualitative — legal on the session plane."""

    id = "toggle"
    on = MorphState(False)

    def render(self):
        on = bool(self.on)
        label = "On" if on else "Off"
        kids = (
            header(
                p("Boolean MorphState", className="kicker"),
                h2("Quiet hours", className="widget-title"),
            ),
            p(
                "The house hushes notifications after dusk."
                if on
                else "Notifications reach the table.",
                className="lede",
            ),
            act(
                "toggle.flip",
                f"Turn {('off' if on else 'on')}",
                kind="primary" if not on else "ghost",
            ),
        )
        if HAS_DOM:
            return div(
                *kids,
                id=self.id,
                className="widget",
                data_on="1" if on else "0",
                aria_pressed="true" if on else "false",
            )
        return f'<div id="{self.id}">{label}</div>'

    @action(caps=())
    def flip(self):
        self.on = not bool(self.on)
        return update_with(self, extra_ops=[notify("on" if self.on else "off")])


class Planes(Component):
    """Side-by-side: mutating only RefState does not morph unless we tick."""

    id = "planes"
    shown = MorphState("hello")
    silent = RefState(0)
    stamp = MorphState("idle")

    def render(self):
        kids = (
            header(
                p("MorphState dirties. RefState does not.", className="kicker"),
                h2("Two planes", className="widget-title"),
            ),
            p(
                span(f"shown · {self.shown}", className="chip"),
                span(f"silent · {int(self.silent or 0)}", className="chip"),
                className="chip-row",
            ),
            div(
                act("planes.morph_only", "Change shown", kind="secondary"),
                act("planes.ref_only", "Bump silent (no tick)", kind="ghost"),
                act("planes.ref_and_tick", "Bump silent + tick", kind="primary"),
                className="row-actions",
            ),
            p(
                "Without a stamp tick, RefState memory changes but the patch "
                "may still look like the previous render if you forget to morph.",
                className="muted",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{self.shown}</div>'

    @action(caps=())
    def morph_only(self):
        self.shown = "hello" if self.shown == "there" else "there"
        return update_with(self)

    @action(caps=())
    def ref_only(self):
        self.silent = int(self.silent or 0) + 1
        # Intentionally no stamp — teaching: view will not change.
        return update_with(self)

    @action(caps=())
    def ref_and_tick(self):
        self.silent = int(self.silent or 0) + 1
        tick(self)
        return update_with(self)


def demo() -> None:
    app = App.boot("Foundation", strict_caps=False)
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
