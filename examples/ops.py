"""Ops / product systems — calendar, progress, copy, settings, offline, presence, KPI, shortcuts.

The last mile of the 99%: operational chrome every working house grows.

    calendar     month is a name; day magnitude in RefState; book is a Cap
    progress     pct RefState; phase named MorphState
    copy         copied bool MorphState; text RefState
    settings     density / motion names; wipe is a Cap
    offline      online bool
    presence     peers list silent; self named
    KPI          values silent; stamp dirties
    shortcuts    same shape as the command palette

No new framework verbs. Morph / Ref / @action / update_with.

Run:
  PYTHONPATH=src:. python examples/ops.py
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
    ul,
    li,
    span,
    section,
)

from examples._common import act, tick, status


class Calendar(Component):
    """Month is a name. Selected day is a magnitude (RefState). Booking is a Cap.

    A grid of 1–28 is Host chrome. Do not put MorphState(14) on the session plane.
    """

    id = "calendar"
    month = MorphState("august")
    day = RefState(20)
    booked = RefState(())
    stamp = MorphState("idle")
    MONTHS = (("july", "July"), ("august", "August"), ("september", "September"))
    DAYS = (14, 15, 20, 21, 27)

    def render(self):
        month = str(self.month or "august")
        day = int(self.day or 20)
        booked = set(int(x) for x in (self.booked or ()))
        months = [
            act(
                "calendar.set_month",
                lab,
                kind="primary" if key == month else "ghost",
                key=key,
            )
            for key, lab in self.MONTHS
        ]
        cells = []
        for d in self.DAYS:
            kind = "primary" if d == day else "ghost"
            label = f"{d}{' ·' if d in booked else ''}"
            cells.append(act("calendar.pick", label, kind=kind, n=str(d)))
        kids = (
            header(
                p("Named month · day silent · book is a Cap", className="kicker"),
                h2("Calendar", className="widget-title"),
            ),
            div(*months, className="seg"),
            p(f"{month} {day}. Dots are already held.", className="lede"),
            div(*cells, className="cal-grid"),
            div(
                act("calendar.book", "Book this day (Cap)", kind="primary"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{month}-{day}</div>'

    @action(caps=())
    def set_month(self, key: str = "august"):
        self.month = key if key in {k for k, _ in self.MONTHS} else "august"
        return update_with(self)

    @action(caps=())
    def pick(self, n: str = "20"):
        try:
            self.day = int(n)
        except ValueError:
            self.day = 20
        tick(self)
        return update_with(self)

    @action(caps=("bookings.create",))
    def book(self):
        d = int(self.day or 0)
        have = tuple(self.booked or ())
        if d and d not in have:
            self.booked = have + (d,)
        tick(self)
        return update_with(self, extra_ops=[notify(f"booked {d}")])


class ProgressMeter(Component):
    """Percent is RefState. Phase is a name (idle / run / done)."""

    id = "progress"
    pct = RefState(0)
    phase = MorphState("idle")
    stamp = MorphState("idle")

    def render(self):
        n = int(self.pct or 0)
        phase = str(self.phase or "idle")
        band = "empty" if n == 0 else "low" if n < 50 else "mid" if n < 100 else "full"
        kids = (
            header(
                p("Pct silent · phase named", className="kicker"),
                h2("Progress", className="widget-title"),
            ),
            p(
                span(f"{n}%", className="num"),
                span(phase, className="chip"),
                className="counter-face",
            ),
            div(className=f"bar bar-{band}"),
            div(
                act("progress.start", "Start", kind="secondary"),
                act("progress.bump", "Advance", kind="primary"),
                act("progress.finish", "Finish", kind="ghost"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_phase=phase)
        return f'<div id="{self.id}">{n}</div>'

    @action(caps=())
    def start(self):
        self.phase = "run"
        self.pct = 10
        tick(self)
        return update_with(self)

    @action(caps=())
    def bump(self):
        n = min(100, int(self.pct or 0) + 25)
        self.pct = n
        self.phase = "done" if n >= 100 else "run"
        tick(self)
        return update_with(self)

    @action(caps=())
    def finish(self):
        self.pct = 100
        self.phase = "done"
        tick(self)
        return update_with(self, extra_ops=[notify("done")])


class CopyClip(Component):
    """Copied is a boolean MorphState. Payload is RefState (not re-painted as MorphState)."""

    id = "copyclip"
    copied = MorphState(False)
    text = RefState("atelier://piece/linen")
    stamp = MorphState("idle")

    def render(self):
        kids = (
            header(
                p("Bool copied · text silent", className="kicker"),
                h2("Copy", className="widget-title"),
            ),
            p(str(self.text or ""), className="lede"),
            status("Copied to the clipboard stand-in.", kind="ok") if self.copied else p(""),
            div(
                act("copyclip.copy", "Copy link", kind="primary"),
                act("copyclip.reset", "Clear flag", kind="text"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def copy(self):
        self.copied = True
        tick(self)
        return update_with(self, extra_ops=[notify("copied")])

    @action(caps=())
    def reset(self):
        self.copied = False
        return update_with(self)


class Settings(Component):
    """Density and motion are names. Wipe is authority (admin.reset lineage)."""

    id = "settings"
    density = MorphState("roomy")
    motion = MorphState("allow")
    stamp = MorphState("idle")

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
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

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
        tick(self)
        return update_with(self, extra_ops=[notify("wiped")])


class OfflineBanner(Component):
    """Connectivity is a boolean MorphState. Copy switches. Not a second Document."""

    id = "offline"
    online = MorphState(True)

    def render(self):
        on = bool(self.online)
        kids = (
            header(
                p("Bool connectivity", className="kicker"),
                h2("Offline banner", className="widget-title"),
            ),
            p(
                "The house is on the wire."
                if on
                else "Working from the table. Actions queue until the wire returns.",
                className="lede",
            ),
            status("Offline — queued.", kind="ok") if not on else p(""),
            act(
                "offline.flip",
                "Go online" if not on else "Cut the wire",
                kind="primary" if on else "secondary",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_online="1" if on else "0")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def flip(self):
        self.online = not bool(self.online)
        return update_with(self, extra_ops=[notify("on" if self.online else "off")])


class Presence(Component):
    """Self status is a name. Peer list is RefState. Typing would be a bool on chat."""

    id = "presence"
    self_state = MorphState("here")
    peers = RefState(("Noor · here", "Atelier · away"))
    stamp = MorphState("idle")

    def render(self):
        me = str(self.self_state or "here")
        lis = [li(x, className="hit") for x in (self.peers or ())]
        kids = (
            header(
                p("Self named · peers silent", className="kicker"),
                h2("Presence", className="widget-title"),
            ),
            p(
                span("You", className="bag-line-name"),
                span(me, className="chip" + (" is-on" if me == "here" else "")),
                className="counter-face",
            ),
            ul(*lis, className="hit-list"),
            div(
                act("presence.set", "Here", kind="primary" if me == "here" else "ghost", key="here"),
                act("presence.set", "Away", kind="primary" if me == "away" else "ghost", key="away"),
                className="seg",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{me}</div>'

    @action(caps=())
    def set(self, key: str = "here"):
        self.self_state = key if key in {"here", "away"} else "here"
        return update_with(self)


class KpiStrip(Component):
    """Dashboard numbers. All magnitudes in RefState. Stamp dirties the strip.

    A real dashboard would source these from Host DB, never from the session plane.
    """

    id = "kpi"
    bag = RefState(3)
    held = RefState(48)
    placed = RefState(2)
    stamp = MorphState("idle")

    def render(self):
        cells = (
            ("In bag", int(self.bag or 0)),
            ("Held", int(self.held or 0)),
            ("Placed", int(self.placed or 0)),
        )
        tiles = [
            section(
                p(label, className="kicker"),
                p(str(n), className="num"),
                className="kpi-tile",
            )
            for label, n in cells
        ]
        kids = (
            header(
                p("Magnitudes silent · stamp dirties", className="kicker"),
                h2("KPI strip", className="widget-title"),
            ),
            div(*tiles, className="kpi-grid"),
            div(
                act("kpi.tick_up", "A sale lands", kind="primary"),
                act("kpi.reset", "Zero the board", kind="text"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def tick_up(self):
        self.bag = max(0, int(self.bag or 0) - 1)
        self.placed = int(self.placed or 0) + 1
        self.held = int(self.held or 0) + 12
        tick(self)
        return update_with(self, extra_ops=[notify("sale")])

    @action(caps=())
    def reset(self):
        self.bag = 0
        self.held = 0
        self.placed = 0
        tick(self)
        return update_with(self)


class Shortcuts(Component):
    """Keyboard overlay. Same encoding as the command palette — query MorphState."""

    id = "shortcuts"
    open = MorphState(False)
    query = MorphState("")
    KEYS = (
        ("g t", "Go to table"),
        ("g b", "Go to bag"),
        ("n", "New note"),
        ("/", "Search"),
        ("?", "Open this overlay"),
    )

    def render(self):
        q = str(self.query or "").lower()
        hits = [(k, lab) for k, lab in self.KEYS if q in k or q in lab.lower()]
        rows = [
            li(
                span(k, className="chip"),
                span(lab),
                className="palette-row",
            )
            for k, lab in hits
        ]
        panel = (
            div(
                p(f"Filter · {q or 'all'}", className="muted"),
                div(
                    act("shortcuts.type", "All", kind="ghost", q=""),
                    act("shortcuts.type", "Go", kind="ghost", q="go"),
                    act("shortcuts.type", "New", kind="ghost", q="new"),
                    className="row-actions",
                ),
                ul(*rows, className="palette-list") if rows else p("No matches.", className="muted"),
                act("shortcuts.close", "Close", kind="ghost"),
                className="palette-panel",
            )
            if self.open
            else act("shortcuts.open_keys", "Open shortcuts", kind="primary")
        )
        kids = (
            header(
                p("Query MorphState", className="kicker"),
                h2("Shortcuts", className="widget-title"),
            ),
            panel,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def open_keys(self):
        self.open = True
        self.query = ""
        return update_with(self)

    @action(caps=())
    def close(self):
        self.open = False
        return update_with(self)

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        self.open = True
        return update_with(self)


def demo() -> None:
    app = App.boot("Ops", strict_caps=False)
    app.add(
        Calendar,
        ProgressMeter,
        CopyClip,
        Settings,
        OfflineBanner,
        Presence,
        KpiStrip,
        Shortcuts,
    )
    print("cal", app.dispatch("calendar.pick", n="21"))
    print("prog", app.dispatch("progress.bump"))
    print("copy", app.dispatch("copyclip.copy"))
    print("set", app.dispatch("settings.set_density", key="compact"))
    print("off", app.dispatch("offline.flip"))
    print("pre", app.dispatch("presence.set", key="away"))
    print("kpi", app.dispatch("kpi.tick_up"))
    print("keys", app.dispatch("shortcuts.open_keys"))
    strict = App.boot("Ops", strict_caps=True)
    strict.add(Calendar, Settings)
    try:
        strict.dispatch("calendar.book")
        print("UNEXPECTED book")
    except Exception as exc:
        print("Cap Law book:", type(exc).__name__)
    try:
        strict.dispatch("settings.wipe")
        print("UNEXPECTED wipe")
    except Exception as exc:
        print("Cap Law wipe:", type(exc).__name__)


if __name__ == "__main__":
    demo()
