"""Breadcrumbs — Trail of named crumbs. Path is a tuple of names — qualitative, not ints.

Ported from the ``shell`` example module (spec §4); that example stays as the teaching copy.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    action,
    notify,
    update_with,
    div,
    h2,
    p,
    header,
    nav,
    span,
)

from ux_compose.author import act

ROUTES = (
    ("table", "Table", "The working surface. Lists morph in place."),
    ("bag", "Bag", "Cart lives here. Checkout is a Cap on that unit."),
    ("inbox", "Inbox", "Badge is a magnitude — dirty + RefState, not MorphState(int)."),
    ("settings", "Settings", "Locale / density are names. Wipe is authority."),
)

class Breadcrumbs(Component):
    """Trail of named crumbs. Path is a tuple of names — qualitative, not ints.

    Clicking a crumb truncates the trail. The last crumb is the page, not a link.
    """

    id = "crumbs"
    path = MorphState(("house", "linen", "workshirt"))
    LABELS = {
        "house": "House",
        "linen": "Linen",
        "oak": "Oak",
        "workshirt": "Work shirt",
        "board": "Serving board",
    }

    def render(self):
        trail = tuple(self.path or ("house",))
        bits = []
        for i, key in enumerate(trail):
            label = self.LABELS.get(key, key)
            last = i == len(trail) - 1
            if last:
                bits.append(span(label, className="crumb is-here"))
            else:
                bits.append(
                    act("crumbs.go", label, kind="text", key=key)
                )
            if not last:
                bits.append(span("/", className="crumb-sep"))
        kids = (
            header(
                p("Tuple of names", className="kicker"),
                h2("Breadcrumbs", className="widget-title"),
            ),
            nav(*bits, className="crumbs", aria_label="Breadcrumb"),
            div(
                act("crumbs.dive", "Open oak / board", kind="ghost", branch="oak"),
                act("crumbs.reset", "Back to house", kind="text"),
                className="row-actions",
            ),
        )
        return div(*kids, id=self.id, className="widget")

    @action(caps=())
    def go(self, key: str = "house"):
        trail = list(self.path or ("house",))
        if key in trail:
            trail = trail[: trail.index(key) + 1]
        else:
            trail = ["house"]
        self.path = tuple(trail)
        return update_with(self, extra_ops=[notify(key)])

    @action(caps=())
    def dive(self, branch: str = "oak"):
        if branch == "oak":
            self.path = ("house", "oak", "board")
        else:
            self.path = ("house", "linen", "workshirt")
        return update_with(self)

    @action(caps=())
    def reset(self):
        self.path = ("house",)
        return update_with(self)


__all__ = ["Breadcrumbs"]
