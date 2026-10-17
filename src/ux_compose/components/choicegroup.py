"""ChoiceGroup — Radio (one name) + checkbox (set of names).

Ported from the ``fields`` example module (spec §4); that example stays as the teaching copy.
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
)

from ux_compose.author import act, mark_dirty

class ChoiceGroup(Component):
    """Radio (one name) + checkbox (set of names).

    Radio value is MorphState (qualitative). Checkbox set is a tuple on
    RefState because it is a list; dirty MorphState dirties.
    """

    id = "choices"
    finish = MorphState("oil")
    extras = RefState(("cloth",))
    dirty = MorphState("idle")
    FINISHES = (("oil", "Oil"), ("wax", "Wax"), ("raw", "Raw"))
    EXTRAS = (("cloth", "Care cloth"), ("box", "Gift box"), ("note", "Hand note"))

    def render(self):
        finish = str(self.finish or "oil")
        picked = set(self.extras or ())
        radios = [
            act(
                "choices.set_finish",
                lab,
                kind="primary" if key == finish else "ghost",
                key=key,
            )
            for key, lab in self.FINISHES
        ]
        checks = [
            act(
                "choices.toggle_extra",
                f"{'✓ ' if key in picked else ''}{lab}",
                kind="secondary" if key in picked else "ghost",
                key=key,
            )
            for key, lab in self.EXTRAS
        ]
        kids = (
            header(
                p("One name · a set of names", className="kicker"),
                h2("Choice group", className="widget-title"),
            ),
            p("Finish is radio. Extras are a set. Neither is a quantity.", className="lede"),
            p("Finish", className="kicker"),
            div(*radios, className="seg", role="radiogroup"),
            p("Extras", className="kicker"),
            div(*checks, className="row-actions"),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def set_finish(self, key: str = "oil"):
        self.finish = key if key in {k for k, _ in self.FINISHES} else "oil"
        return update_with(self, extra_ops=[notify(self.finish)])

    @action(caps=())
    def toggle_extra(self, key: str = ""):
        cur = set(self.extras or ())
        if key in cur:
            cur.remove(key)
        elif key:
            cur.add(key)
        self.extras = tuple(sorted(cur))
        mark_dirty(self)
        return update_with(self)


__all__ = ["ChoiceGroup"]
