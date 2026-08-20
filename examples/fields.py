"""Form fields — the remaining 99% of inputs.

Signup / wizard / typeahead live in ``forms.py``. This file is every other
control a product actually ships:

    radio / checkbox set     names in RefState + stamp
    combobox                 query MorphState + value MorphState
    date                     named window MorphState; ISO in RefState
    file drop                filenames RefState + stamp
    slider                   magnitude RefState + stamp
    OTP                      digits RefState; verify is a Cap
    password reveal          bool MorphState; secret RefState
    autosave                 dirty MorphState; draft RefState
    limited note             length derived from RefState

Never put ints / money / counts on MorphState if the class will go live
(Channel session plane refuses quantity). Named steps, bools, and short
strings are legal.

Validation is public. The verb that *creates / charges / verifies identity*
is Cap-protected.

Run:
  PYTHONPATH=src:. python examples/fields.py
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
    form,
    button,
    control,
)

from examples._common import act, field, tick, status


class ChoiceGroup(Component):
    """Radio (one name) + checkbox (set of names).

    Radio value is MorphState (qualitative). Checkbox set is a tuple on
    RefState because it is a list; stamp dirties.
    """

    id = "choices"
    finish = MorphState("oil")
    extras = RefState(("cloth",))
    stamp = MorphState("idle")
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
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{finish}</div>'

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
        tick(self)
        return update_with(self)


class Combobox(Component):
    """Type to filter, then pick one. Query and value are both MorphState.

    Offline we filter a Host tuple. Live would debounce on the Host with a
    RefState request token (see Search in forms.py).
    """

    id = "combobox"
    query = MorphState("")
    value = MorphState("")
    open = MorphState(False)
    OPTIONS = ("Linen work shirt", "Oak serving board", "Wool throw", "Clay pourer", "Oak stool")

    def render(self):
        q = str(self.query or "")
        val = str(self.value or "")
        hits = [x for x in self.OPTIONS if q.lower() in x.lower()] if q else list(self.OPTIONS)
        rows = [
            li(
                act("combobox.pick", x, kind="text", key=x),
                className="palette-row",
                id=f"combo-{i}",
            )
            for i, x in enumerate(hits[:6])
        ]
        kids = (
            header(
                p("Query + value MorphState", className="kicker"),
                h2("Combobox", className="widget-title"),
            ),
            p(f"Chosen · {val or 'none'}", className="muted"),
            form(
                field("q", q, placeholder="Filter pieces"),
                button("Filter", type="submit", className="btn-primary", **control("combobox.type")),
                method="post",
                action="/act/combobox.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            ul(*rows, className="palette-list")
            if self.open and rows
            else (p("No matches.", className="muted") if self.open else span("", className="sr")),
            act("combobox.clear", "Clear", kind="text"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{val}</div>'

    @action(caps=())
    def type(self, q: str = ""):
        self.query = q
        self.open = True
        return update_with(self)

    @action(caps=())
    def pick(self, key: str = ""):
        self.value = key
        self.query = key
        self.open = False
        return update_with(self, extra_ops=[notify(key)])

    @action(caps=())
    def clear(self):
        self.query = ""
        self.value = ""
        self.open = False
        return update_with(self)


class DateField(Component):
    """Dates are not ints. Window is a name; ISO lives in RefState.

    Channel would refuse MorphState(20260820). Named windows survive.
    """

    id = "datefield"
    window = MorphState("today")
    iso = RefState("2026-08-20")
    stamp = MorphState("idle")
    WINDOWS = (
        ("today", "Today", "2026-08-20"),
        ("tomorrow", "Tomorrow", "2026-08-21"),
        ("week", "Next week", "2026-08-27"),
    )

    def render(self):
        win = str(self.window or "today")
        segs = [
            act(
                "datefield.set_window",
                lab,
                kind="primary" if key == win else "ghost",
                key=key,
            )
            for key, lab, _ in self.WINDOWS
        ]
        kids = (
            header(
                p("Named window · ISO silent", className="kicker"),
                h2("Date", className="widget-title"),
            ),
            p(f"ISO on the Host plane · {self.iso}", className="lede"),
            div(*segs, className="seg"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_window=win)
        return f'<div id="{self.id}">{win}</div>'

    @action(caps=())
    def set_window(self, key: str = "today"):
        row = {k: iso for k, _, iso in self.WINDOWS}.get(key)
        if row is None:
            key, row = "today", "2026-08-20"
        self.window = key
        self.iso = row
        tick(self)
        return update_with(self, extra_ops=[notify(row)])


class FileDrop(Component):
    """Filenames in RefState. Count is derived. Upload-commit would take a Cap.

    Real bytes never live on the Component. Host owns the store.
    """

    id = "filedrop"
    files = RefState(())
    stamp = MorphState("idle")

    def render(self):
        rows = list(self.files or ())
        lis = [
            li(
                span(name, className="bag-line-name"),
                act("filedrop.remove", "Remove", kind="text", name=name),
                id=f"file-{i}",
                className="bag-line",
            )
            for i, name in enumerate(rows)
        ] or [li("Drop zone empty. Add a named stand-in.", className="muted")]
        kids = (
            header(
                p("Names in RefState · bytes on Host", className="kicker"),
                h2("File drop", className="widget-title"),
            ),
            p(f"{len(rows)} file(s). The Component never holds bytes.", className="lede"),
            ul(*lis, className="bag-lines"),
            div(
                act("filedrop.add", "Add linen.jpg", kind="secondary", name="linen.jpg"),
                act("filedrop.add", "Add oak.pdf", kind="secondary", name="oak.pdf"),
                act("filedrop.clear", "Clear", kind="text"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget file-drop")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def add(self, name: str = ""):
        name = (name or "").strip()
        if name and name not in (self.files or ()):
            self.files = tuple(self.files or ()) + (name,)
        tick(self)
        return update_with(self, extra_ops=[notify(name)])

    @action(caps=())
    def remove(self, name: str = ""):
        self.files = tuple(x for x in (self.files or ()) if x != name)
        tick(self)
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.files = ()
        tick(self)
        return update_with(self)


class SliderField(Component):
    """Magnitude in RefState. Named band is derived, never stored as an int MorphState."""

    id = "slider"
    value = RefState(40)
    stamp = MorphState("idle")
    STEPS = (0, 25, 50, 75, 100)

    def render(self):
        v = int(self.value or 0)
        band = "empty" if v == 0 else "low" if v < 50 else "mid" if v < 100 else "full"
        segs = [
            act(
                "slider.set",
                str(n),
                kind="primary" if n == v else "ghost",
                n=str(n),
            )
            for n in self.STEPS
        ]
        kids = (
            header(
                p("RefState magnitude · named band derived", className="kicker"),
                h2("Slider", className="widget-title"),
            ),
            p(
                span(f"{v}%", className="num"),
                span(band, className="chip"),
                className="counter-face",
            ),
            div(className=f"bar bar-{band}"),
            div(*segs, className="seg"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{v}</div>'

    @action(caps=())
    def set(self, n: str = "40"):
        try:
            v = int(n)
        except ValueError:
            v = 40
        self.value = max(0, min(100, v))
        tick(self)
        return update_with(self)


class OtpGate(Component):
    """Identity check. Digits are RefState. Verify is Cap-protected.

    Typing is public (it only paints). Crossing the gate spends authority.
    """

    id = "otpgate"
    digits = RefState("")
    error = MorphState("")
    ok = MorphState(False)
    stamp = MorphState("idle")
    EXPECT = "2468"

    def render(self):
        d = str(self.digits or "")
        shown = (d + "····")[:4]
        kids = (
            header(
                p("Digits silent · verify is a Cap", className="kicker"),
                h2("OTP gate", className="widget-title"),
            ),
            p("Stand-in code for the studio: 2468. Live Host would SMS it.", className="lede"),
            p(shown, className="num otp-face"),
            form(
                field("code", d, placeholder="4 digits", kind="text"),
                button("Hold digits", type="submit", className="btn-secondary", **control("otpgate.type")),
                method="post",
                action="/act/otpgate.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            div(
                act("otpgate.type", "Fill 2468", kind="ghost", code="2468"),
                act("otpgate.verify", "Verify (Cap)", kind="primary"),
                act("otpgate.reset", "Clear", kind="text"),
                className="row-actions",
            ),
            p(str(self.error), className="error", role="alert") if self.error else p(""),
            status("Gate open.", kind="ok") if self.ok else p(""),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def type(self, code: str = ""):
        self.digits = "".join(ch for ch in str(code or "") if ch.isdigit())[:4]
        self.error = ""
        self.ok = False
        tick(self)
        return update_with(self)

    @action(caps=())
    def reset(self):
        self.digits = ""
        self.error = ""
        self.ok = False
        tick(self)
        return update_with(self)

    @action(caps=("auth.verify",))
    def verify(self):
        if str(self.digits or "") != self.EXPECT:
            self.error = "Code does not match"
            self.ok = False
            tick(self)
            return update_with(self, extra_ops=[notify("mismatch")])
        self.ok = True
        self.error = ""
        tick(self)
        return update_with(self, extra_ops=[notify("verified")])


class PasswordField(Component):
    """Reveal is boolean MorphState. The secret itself is RefState (not painted as MorphState)."""

    id = "password"
    shown = MorphState(False)
    secret = RefState("")
    stamp = MorphState("idle")

    def render(self):
        shown = bool(self.shown)
        raw_s = str(self.secret or "")
        face = raw_s if shown else ("•" * len(raw_s) if raw_s else "empty")
        kids = (
            header(
                p("Bool reveal · secret silent", className="kicker"),
                h2("Password", className="widget-title"),
            ),
            p(face, className="lede"),
            form(
                field("secret", raw_s if shown else "", placeholder="Passphrase", kind="text"),
                button("Hold", type="submit", className="btn-secondary", **control("password.set")),
                method="post",
                action="/act/password.set",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            div(
                act("password.toggle", "Hide" if shown else "Reveal", kind="ghost"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def set(self, secret: str = ""):
        self.secret = secret
        tick(self)
        return update_with(self)

    @action(caps=())
    def toggle(self):
        self.shown = not bool(self.shown)
        return update_with(self)


class Autosave(Component):
    """Dirty flag MorphState. Draft body RefState. Saved stamp is a name.

    Debounce lives on the Host. Behavior only holds the window.
    """

    id = "autosave"
    dirty = MorphState(False)
    draft = RefState("Quiet pieces for a working house.")
    saved = MorphState("clean")
    stamp = MorphState("idle")

    def render(self):
        kids = (
            header(
                p("Dirty flag · draft silent", className="kicker"),
                h2("Autosave", className="widget-title"),
            ),
            p(str(self.draft or ""), className="lede"),
            p(
                "Unsaved changes." if self.dirty else f"Saved · {self.saved}.",
                className="muted",
            ),
            form(
                field("text", str(self.draft or ""), placeholder="Draft"),
                button("Type", type="submit", className="btn-secondary", **control("autosave.type")),
                method="post",
                action="/act/autosave.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            div(
                act("autosave.type", "Edit a line", kind="ghost", text="Held until you place."),
                act("autosave.save", "Save now", kind="primary"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_dirty="1" if self.dirty else "0")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def type(self, text: str = ""):
        if text:
            self.draft = text
        self.dirty = True
        self.saved = "dirty"
        tick(self)
        return update_with(self)

    @action(caps=())
    def save(self):
        self.dirty = False
        self.saved = "just-now"
        tick(self)
        return update_with(self, extra_ops=[notify("saved")])


class LimitedNote(Component):
    """Remaining characters are *derived*. Store the text, not the count, as MorphState."""

    id = "limited"
    text = RefState("")
    stamp = MorphState("idle")
    LIMIT = 80

    def render(self):
        t = str(self.text or "")
        left = max(0, self.LIMIT - len(t))
        over = len(t) > self.LIMIT
        kids = (
            header(
                p("Count is derived", className="kicker"),
                h2("Limited note", className="widget-title"),
            ),
            p(t or "Write a short note for the maker.", className="lede"),
            p(
                f"{left} left" if not over else f"{len(t) - self.LIMIT} over",
                className="error" if over else "muted",
            ),
            form(
                field("text", t, placeholder="Up to 80 characters"),
                button("Hold", type="submit", className="btn-primary", **control("limited.type")),
                method="post",
                action="/act/limited.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            div(
                act("limited.type", "Short line", kind="ghost", text="Please oil the board."),
                act("limited.type", "Over-limit", kind="ghost", text="x" * 90),
                act("limited.clear", "Clear", kind="text"),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}"></div>'

    @action(caps=())
    def type(self, text: str = ""):
        self.text = text
        tick(self)
        return update_with(self)

    @action(caps=())
    def clear(self):
        self.text = ""
        tick(self)
        return update_with(self)


def demo() -> None:
    app = App.boot("Fields", strict_caps=False)
    app.add(
        ChoiceGroup,
        Combobox,
        DateField,
        FileDrop,
        SliderField,
        OtpGate,
        PasswordField,
        Autosave,
        LimitedNote,
    )
    print("finish", app.dispatch("choices.set_finish", key="wax"))
    print("combo", app.dispatch("combobox.pick", key="Wool throw"))
    print("date", app.dispatch("datefield.set_window", key="week"))
    print("file", app.dispatch("filedrop.add", name="linen.jpg"))
    print("slider", app.dispatch("slider.set", n="75"))
    print("otp", app.dispatch("otpgate.type", code="2468"))
    print("pass", app.dispatch("password.set", secret="held"))
    print("auto", app.dispatch("autosave.type", text="draft"))
    print("note", app.dispatch("limited.type", text="hello"))
    strict = App.boot("Fields", strict_caps=True)
    strict.add(OtpGate)
    try:
        strict.dispatch("otpgate.verify")
        print("UNEXPECTED verify")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
