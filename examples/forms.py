"""Forms — field errors, wizard, search/typeahead.

Validation is MorphState (must repaint). Attempt counters are RefState.
The submit that *creates* an account is Cap-protected; checking an email is not.

Wizard: step MorphState as a name, not an int (Channel plane). Payload in RefState.

Run:
  PYTHONPATH=src:. python examples/forms.py
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
    form,
    button,
    control,
    span,
)

from examples._common import act, field, tick


class SignupForm(Component):
    id = "signup"
    email = MorphState("")
    error = MorphState("")
    ok = MorphState(False)
    attempts = RefState(0)

    def render(self):
        err = str(self.error or "")
        kids = (
            header(
                p("Errors are MorphState", className="kicker"),
                h2("Sign up", className="widget-title"),
            ),
            p("Validate publicly. Create the account under a Cap.", className="lede"),
            form(
                field("email", str(self.email or ""), placeholder="you@atelier.test"),
                button(
                    "Submit",
                    type="submit",
                    className="btn-primary",
                    **control("signup.submit"),
                ),
                method="post",
                action="/act/signup.submit",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            p(err, className="error", role="alert") if err else p(""),
            p("Welcome. The host would mint account.create here.", className="status status-ok")
            if self.ok
            else p(""),
            act("signup.create_account", "Create account (Cap)", kind="ghost"),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<form id="{self.id}"><p>{err}</p></form>'

    @action(caps=())
    def submit(self, email: str = ""):
        self.attempts = int(self.attempts or 0) + 1
        self.email = (email or self.email or "").strip()
        self.ok = False
        if "@" not in str(self.email) or "." not in str(self.email).split("@")[-1]:
            self.error = "Enter a valid email"
            return update_with(self, extra_ops=[notify("invalid")])
        self.error = ""
        self.ok = True
        return update_with(self, extra_ops=[notify(f"ok {self.email}")])

    @action(caps=("account.create",))
    def create_account(self):
        if not self.ok:
            self.error = "Submit a valid email first"
            return update_with(self, extra_ops=[notify("blocked")])
        return update_with(self, extra_ops=[notify("account created")])


class Wizard(Component):
    """Named steps, not integers. Payload rides in RefState until the last verb."""

    id = "wizard"
    step = MorphState("who")
    name = RefState("")
    piece = RefState("linen")
    stamp = MorphState("idle")

    STEPS = ("who", "piece", "review")

    def render(self):
        step = str(self.step or "who")
        body = []
        if step == "who":
            body = [
                p("Who is the order for?", className="lede"),
                form(
                    field("name", str(self.name or ""), placeholder="Name"),
                    button("Continue", type="submit", className="btn-primary", **control("wizard.next")),
                    method="post",
                    action="/act/wizard.next",
                    data_ux="1",
                    data_target="#stage",
                    className="stack",
                )
                if HAS_DOM
                else p(""),
            ]
        elif step == "piece":
            body = [
                p(f"Hello {self.name or 'friend'}. Pick a piece.", className="lede"),
                div(
                    act("wizard.choose", "Linen", kind="secondary", piece="linen"),
                    act("wizard.choose", "Oak", kind="secondary", piece="oak"),
                    act("wizard.choose", "Wool", kind="secondary", piece="wool"),
                    className="row-actions",
                ),
            ]
        else:
            body = [
                p(
                    f"{self.name or 'Friend'} · {self.piece}. Placing the order is a Cap.",
                    className="lede",
                ),
                act("wizard.place", "Place order", kind="primary"),
                act("wizard.back", "Back", kind="text"),
            ]
        kids = (
            header(
                p(f"Step {step}", className="kicker"),
                h2("Wizard", className="widget-title"),
            ),
            *body,
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget", data_step=step)
        return f'<div id="{self.id}">{step}</div>'

    @action(caps=())
    def next(self, name: str = ""):
        if name:
            self.name = name
        if not str(self.name or "").strip():
            return update_with(self, extra_ops=[notify("name required")])
        self.step = "piece"
        tick(self)
        return update_with(self)

    @action(caps=())
    def choose(self, piece: str = "linen"):
        self.piece = piece
        self.step = "review"
        tick(self)
        return update_with(self)

    @action(caps=())
    def back(self):
        order = list(self.STEPS)
        i = max(0, order.index(self.step) - 1) if self.step in order else 0
        self.step = order[i]
        return update_with(self)

    @action(caps=("orders.place",))
    def place(self):
        self.step = "who"
        self.name = ""
        tick(self)
        return update_with(self, extra_ops=[notify("placed")])


class Search(Component):
    """Typeahead / debounced search. Query MorphState; hits RefState; token RefState.

    Stale responses: bump ``req`` on every type. Ignore results whose token
    no longer matches (Host async). Offline we filter a local catalog.
    """

    id = "search"
    query = MorphState("")
    hits = RefState(())
    req = RefState(0)
    stamp = MorphState("idle")
    CATALOG = ("Work shirt", "Serving board", "Throw", "Pourer", "Oak stool", "Wool cap")

    def render(self):
        q = str(self.query or "")
        rows = list(self.hits or ())
        lis = [li(x, className="hit") for x in rows] or [
            li("Type to filter the table.", className="muted")
        ]
        kids = (
            header(
                p("Stale-token guard on RefState", className="kicker"),
                h2("Search", className="widget-title"),
            ),
            form(
                field("q", q, placeholder="Filter pieces"),
                button("Search", type="submit", className="btn-primary", **control("search.type")),
                method="post",
                action="/act/search.type",
                data_ux="1",
                data_target="#stage",
                className="stack",
            )
            if HAS_DOM
            else p(""),
            ul(*lis, className="hit-list"),
            div(
                act("search.type", "Oak", kind="ghost", q="oak"),
                act("search.type", "Wool", kind="ghost", q="wool"),
                act("search.type", "Clear", kind="text", q=""),
                className="row-actions",
            ),
        )
        if HAS_DOM:
            return div(*kids, id=self.id, className="widget")
        return f'<div id="{self.id}">{q}</div>'

    @action(caps=())
    def type(self, q: str = ""):
        self.req = int(self.req or 0) + 1
        token = self.req
        self.query = q
        qn = q.lower()
        found = tuple(x for x in self.CATALOG if qn in x.lower()) if qn else ()
        if token != self.req:
            return []
        self.hits = found
        tick(self)
        return update_with(self)


def demo() -> None:
    app = App.boot("Forms", strict_caps=False)
    app.add(SignupForm, Wizard, Search)
    print("bad", app.dispatch("signup.submit", email="nope"))
    print("ok", app.dispatch("signup.submit", email="you@atelier.test"))
    print("wiz", app.dispatch("wizard.next", name="Noor"))
    print("search", app.dispatch("search.type", q="oak"))
    strict = App.boot("Forms", strict_caps=True)
    strict.add(SignupForm)
    try:
        strict.dispatch("signup.create_account")
        print("UNEXPECTED")
    except Exception as exc:
        print("Cap Law:", type(exc).__name__)


if __name__ == "__main__":
    demo()
