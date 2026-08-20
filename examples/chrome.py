"""Chrome widgets — Tabs, Accordion, Dropdown, Drawer.

99% of product chrome is open/value MorphState + public @action.
No Caps unless the verb spends money, deletes, or changes identity.

Stable ids on panels (``#tab-cut``) let Motion stagger later without rewrite.

Run:
  PYTHONPATH=src:. python examples/chrome.py
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
    section,
    span,
)

from examples._common import act, maybe_fade

TABS = (
    ("cut", "Cut", "The pattern book. Tabs morph one region; they do not remount the page."),
    ("make", "Make", "Actions stay on the same Component. Motion, when unlocked, is a Plan."),
    ("keep", "Keep", "Caps stay off chrome. Opening a tab is not an authority event."),
)


class Tabs(Component):
    id = "tabs"
    tab = MorphState("cut")

    def render(self):
        current = str(self.tab or "cut")
        panels = {k: (title, body) for k, title, body in TABS}
        title, body = panels.get(current, panels["cut"])
        segs = []
        for key, label, _ in TABS:
            segs.append(
                act(
                    "tabs.select",
                    label,
                    kind="primary" if key == current else "ghost",
                    tab=key,
                )
            )
        kids = (
            header(
                p("One MorphState key", className="kicker"),
                h2("Tabs", className="widget-title"),
            ),
            div(*segs, className="seg", role="tablist"),
            section(
                h2(title),
                p(body, className="lede"),
                id=f"tab-{current}",
                className="tab-panel",
                role="tabpanel",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_tab=current)
        return f'<div id="{self.id}">{current}</div>'

    @action(caps=())
    def select(self, tab: str = "cut"):
        if tab not in {k for k, _, _ in TABS}:
            tab = "cut"
        self.tab = tab
        return update_with(
            self,
            maybe_fade("tab-in", f"#tab-{tab}", ms=100),
            extra_ops=[notify(tab)],
        )


class Accordion(Component):
    """Several panels may be open. Store open ids as a tuple on MorphState.

    Tuples are qualitative identity sets, not quantities.
    """

    id = "accordion"
    open_ids = MorphState(("fit",))

    SECTIONS = (
        ("fit", "Fit", "One Component owns the open set. Nested pages do not."),
        ("law", "Law", "XOR: morph this unit; never put html= on scene.enter for #accordion."),
        ("cap", "Cap", "Reading a section is public. Publishing it would take a Cap."),
    )

    def render(self):
        opened = tuple(self.open_ids or ())
        items = []
        for key, title, body in self.SECTIONS:
            is_open = key in opened
            items.append(
                section(
                    act(
                        "accordion.toggle",
                        f"{'Hide' if is_open else 'Show'} {title}",
                        kind="text",
                        key=key,
                    ),
                    p(body, className="lede") if is_open else p(""),
                    className="acc-item" + (" is-open" if is_open else ""),
                    id=f"acc-{key}",
                )
            )
        kids = (
            header(
                p("Set of open ids", className="kicker"),
                h2("Accordion", className="widget-title"),
            ),
            *items,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def toggle(self, key: str = ""):
        cur = set(self.open_ids or ())
        if key in cur:
            cur.remove(key)
        elif key:
            cur.add(key)
        self.open_ids = tuple(sorted(cur))
        return update_with(self)


class Dropdown(Component):
    """Open flag + selected value. Click-away is Host JS; state stays here."""

    id = "dropdown"
    open = MorphState(False)
    value = MorphState("linen")

    OPTIONS = (("linen", "Linen"), ("oak", "Oak"), ("wool", "Wool"), ("clay", "Clay"))

    def render(self):
        val = str(self.value or "linen")
        label = dict(self.OPTIONS).get(val, val)
        options = [
            act("dropdown.choose", lab, kind="text", key=key)
            for key, lab in self.OPTIONS
        ]
        menu = (
            div(*options, className="menu", role="listbox")
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Menu is MorphState(open)", className="kicker"),
                h2("Dropdown", className="widget-title"),
            ),
            div(
                act(
                    "dropdown.toggle",
                    f"{label} ▾",
                    kind="secondary",
                ),
                menu,
                className="dropdown-wrap",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_open="1" if self.open else "0")
        return f'<div id="{self.id}">{val}</div>'

    @action(caps=())
    def toggle(self):
        self.open = not bool(self.open)
        return update_with(self)

    @action(caps=())
    def choose(self, key: str = "linen"):
        self.value = key
        self.open = False
        return update_with(self, extra_ops=[notify(key)])


class Drawer(Component):
    """Sheet from the side. Same shape as a modal — different CSS."""

    id = "drawer"
    open = MorphState(False)
    which = RefState("filters")

    def render(self):
        panel = (
            div(
                h2("Filters"),
                p("Drawer content is just render(). Closing morphs it away.", className="lede"),
                act("drawer.close", "Close", kind="ghost"),
                className="drawer-panel",
            )
            if self.open
            else span("", className="sr")
        )
        kids = (
            header(
                p("Presence flag", className="kicker"),
                h2("Drawer", className="widget-title"),
            ),
            act("drawer.open_drawer", "Open filters", kind="primary"),
            panel,
        )
        if HAS_DOM:
            return div(
                *kids,
                id=self.id,
                className="widget drawer" + (" is-open" if self.open else ""),
                data_open="1" if self.open else "0",
            )
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def open_drawer(self, which: str = "filters"):
        self.open = True
        self.which = which
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)


def demo() -> None:
    app = App.boot("Chrome", strict_caps=False)
    app.add(Tabs, Accordion, Dropdown, Drawer)
    print("tabs", app.dispatch("tabs.select", tab="make"))
    print("acc", app.dispatch("accordion.toggle", key="law"))
    print("drop", app.dispatch("dropdown.choose", key="oak"))
    print("drawer", app.dispatch("drawer.open_drawer"))


if __name__ == "__main__":
    demo()
