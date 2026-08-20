"""Shell chrome — app frame, breadcrumbs, bottom nav, popover, overflow.

99% of product *frames* are the same two MorphState keys:

    current / open / collapsed   qualitative MorphState
    last-clicked payload         RefState + stamp (if a magnitude or list)

A shell is **not** a second Document. One HTML shell, many units. Opening a
route is public. Spending money / deleting / changing identity is a Cap on
the *destination* Component, never on the nav chrome.

Stable ids (``#shell-table``, ``#crumb-linen``) survive morph so Motion can
later address the surviving region with zero rewrite.

Run:
  PYTHONPATH=src:. python examples/shell.py
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
    nav,
    section,
    span,
    ul,
    li,
)

from examples._common import act, tick


ROUTES = (
    ("table", "Table", "The working surface. Lists morph in place."),
    ("bag", "Bag", "Cart lives here. Checkout is a Cap on that unit."),
    ("inbox", "Inbox", "Badge is a magnitude — stamp + RefState, not MorphState(int)."),
    ("settings", "Settings", "Locale / density are names. Wipe is authority."),
)


class AppShell(Component):
    """Sidebar + current region. Collapsed is a boolean MorphState (legal live).

    Why not four Components? Because the verbs (go, collapse) belong to one
    unit. Split only when a region grows its own protected verbs.
    """

    id = "appshell"
    current = MorphState("table")
    collapsed = MorphState(False)

    def render(self):
        cur = str(self.current or "table")
        copy = {k: (title, body) for k, title, body in ROUTES}
        title, body = copy.get(cur, copy["table"])
        links = [
            act(
                "appshell.go",
                label,
                kind="primary" if key == cur else "ghost",
                key=key,
            )
            for key, label, _ in ROUTES
        ]
        kids = (
            header(
                p("Named route · bool collapsed", className="kicker"),
                h2("App shell", className="widget-title"),
            ),
            p(
                "Press a region. The page does not remount. Caps stay off chrome.",
                className="lede",
            ),
            div(
                nav(*links, className="seg", aria_label="Primary"),
                act(
                    "appshell.toggle",
                    "Expand rail" if self.collapsed else "Collapse rail",
                    kind="text",
                ),
                className="shell-rail" + (" is-collapsed" if self.collapsed else ""),
            ),
            section(
                h2(title),
                p(body, className="lede"),
                p(
                    "Rail is " + ("narrow." if self.collapsed else "open."),
                    className="muted",
                ),
                id=f"shell-{cur}",
                className="tab-panel",
            ),
        )
        if HAS_DOM:
            return div(
                *kids,
                id=self.id,
                className="widget",
                data_current=cur,
                data_collapsed="1" if self.collapsed else "0",
            )
        return f'<div id="{self.id}">{cur}</div>'

    @action(caps=())
    def go(self, key: str = "table"):
        if key not in {k for k, _, _ in ROUTES}:
            key = "table"
        self.current = key
        return update_with(self, extra_ops=[notify(key)])

    @action(caps=())
    def toggle(self):
        self.collapsed = not bool(self.collapsed)
        return update_with(self)


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
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{trail[-1]}</div>'

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


class BottomNav(Component):
    """Mobile tab bar. Same encoding as Tabs — one named MorphState key.

    Four destinations is the product ceiling. A fifth item becomes overflow.
    """

    id = "bottomnav"
    tab = MorphState("home")
    TABS = (
        ("home", "Home", "The table of the week."),
        ("search", "Search", "Typeahead lives on its own unit."),
        ("bag", "Bag", "Count is a badge on the destination, not here."),
        ("you", "You", "Account chrome. Sign-out would take a Cap."),
    )

    def render(self):
        cur = str(self.tab or "home")
        copy = {k: body for k, _, body in self.TABS}
        segs = [
            act(
                "bottomnav.select",
                label,
                kind="primary" if key == cur else "ghost",
                key=key,
            )
            for key, label, _ in self.TABS
        ]
        kids = (
            header(
                p("Four named destinations", className="kicker"),
                h2("Bottom nav", className="widget-title"),
            ),
            p(copy.get(cur, ""), className="lede"),
            nav(*segs, className="bottom-nav", aria_label="Sections"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_tab=cur)
        return f'<div id="{self.id}">{cur}</div>'

    @action(caps=())
    def select(self, key: str = "home"):
        if key not in {k for k, _, _ in self.TABS}:
            key = "home"
        self.tab = key
        return update_with(self, extra_ops=[notify(key)])


class Popover(Component):
    """Anchored panel. Open is MorphState. Pin (which row) is MorphState too.

    Click-away is Host JS. State stays on the Component. Not a modal — the
    rest of the page stays interactive. Document SSoT still holds.
    """

    id = "popover"
    open = MorphState(False)
    pin = MorphState("cut")
    PINS = (("cut", "Cut list"), ("make", "Make list"), ("keep", "Keep list"))

    def render(self):
        pin = str(self.pin or "cut")
        label = dict(self.PINS).get(pin, pin)
        panel = (
            div(
                p(f"Pinned to {label}.", className="lede"),
                div(
                    *[
                        act("popover.pin_to", lab, kind="text", key=key)
                        for key, lab in self.PINS
                    ],
                    className="menu",
                    role="menu",
                ),
                act("popover.close", "Close", kind="ghost"),
                className="popover-panel",
            )
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Open flag + named pin", className="kicker"),
                h2("Popover", className="widget-title"),
            ),
            div(
                act(
                    "popover.toggle",
                    f"{label} ▾" if not self.open else "Hide",
                    kind="secondary",
                ),
                panel,
                className="dropdown-wrap",
            ),
        )
        if HAS_DOM:
            return div(
                *kids,
                id=self.id,
                className="widget",
                data_open="1" if self.open else "0",
            )
        return f'<div id="{self.id}">{pin}</div>'

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def pin_to(self, key: str = "cut"):
        self.pin = key
        self.open = True
        return update_with(self, extra_ops=[notify(key)])

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)


class OverflowMenu(Component):
    """Kebab / ⋯ menu. Presence is MorphState. Chosen verb is a public dispatch.

    Destructive items inside an overflow still take a Cap on *their* action,
    not on opening the menu.
    """

    id = "overflow"
    open = MorphState(False)
    last = RefState("")
    stamp = MorphState("idle")

    def render(self):
        last = str(self.last or "—")
        menu = (
            div(
                act("overflow.choose", "Duplicate", kind="text", key="duplicate"),
                act("overflow.choose", "Move to Keep", kind="text", key="move"),
                act("overflow.choose", "Archive (Cap)", kind="text", key="archive"),
                className="menu",
                role="menu",
            )
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Open is MorphState · last is silent", className="kicker"),
                h2("Overflow", className="widget-title"),
            ),
            p(f"Last verb · {last}", className="muted"),
            div(
                act("overflow.toggle", "⋯", kind="secondary"),
                menu,
                className="dropdown-wrap",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{last}</div>'

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def choose(self, key: str = ""):
        """Archive is demonstrated as a *named* choice here.

        The real archive verb lives on the table unit with caps records.archive.
        Overflow records intent; it does not spend authority.
        """
        self.last = key
        self.open = False
        tick(self)
        return update_with(self, extra_ops=[notify(key or "none")])


def demo() -> None:
    app = App.boot("Shell", strict_caps=False)
    app.add(AppShell, Breadcrumbs, BottomNav, Popover, OverflowMenu)
    print("go", app.dispatch("appshell.go", key="bag"))
    print("crumb", app.dispatch("crumbs.go", key="linen"))
    print("nav", app.dispatch("bottomnav.select", key="search"))
    print("pop", app.dispatch("popover.pin_to", key="keep"))
    print("over", app.dispatch("overflow.choose", key="duplicate"))


if __name__ == "__main__":
    demo()
