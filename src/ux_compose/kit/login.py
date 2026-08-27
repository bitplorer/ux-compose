"""Drop-in login card — MorphState chrome, RefState secrets, Cap on submit.

Show/Hide and tab switches attach live form values onto RefState *before*
the morph, so the new input paints with ``value=``. The secret never lives
on MorphState.

Host seam: override ``authenticate()``. Validation and reveal stay here.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from typing import NamedTuple

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    bind,
    notify,
    update_with,
    div,
    span,
    button,
    form,
    input_,
    label,
    p,
    h1,
)


class AuthDecision(NamedTuple):
    """Return value of ``Login.authenticate``."""

    ok: bool
    message: str = ""
    blocked: bool = False


def _email_ok(value: str) -> bool:
    v = (value or "").strip()
    return "@" in v and "." in v.split("@")[-1] and len(v) >= 5


def _password_ok(value: str, *, signup: bool) -> bool:
    v = value or ""
    if len(v) < 8:
        return False
    if signup and not any(c.isdigit() for c in v):
        return False
    return True


class Login(Component):
    """Sign-in / sign-up card. Copy, ``app.add(Login)``, or subclass.

    Chrome is MorphState. Values and field errors are RefState. Submit
    spends ``auth.login`` / ``auth.signup``. Reveal and mode switches are
    public — they attach typed values, then morph.

    Demo stand-in: any valid email/password signs in; ``@blocked.test``
    fails closed. Override ``authenticate()`` in the product.
    """

    id = "login"

    class_card = (
        "[grid-area:card] self-center mx-auto flex w-full max-w-md flex-col rounded-3xl border "
        "border-stone-200 bg-white p-8 text-stone-900 shadow-sm"
    )
    class_head = "mb-8"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "mt-1.5 mb-0 text-sm leading-relaxed text-stone-500"
    class_tabs = "mb-6 grid grid-cols-2 gap-1 rounded-full bg-stone-100 p-1"
    class_tab = (
        "min-h-11 cursor-pointer rounded-full border-0 bg-transparent "
        "px-4 text-sm font-medium text-stone-500 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_tab_on = (
        "min-h-11 cursor-pointer rounded-full border-0 bg-white "
        "px-4 text-sm font-medium text-stone-900 shadow-sm "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_alert = "mb-4 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3"
    class_alert_text = "text-sm text-rose-700"
    class_form = "flex flex-col gap-4"
    class_field = "flex flex-col gap-1.5"
    class_label = "text-sm font-medium"
    class_input = (
        "w-full min-h-11 rounded-2xl border border-stone-200 bg-stone-50 "
        "px-4 py-3 text-sm text-stone-900 outline-none "
        "focus:border-stone-400 focus:bg-white focus:ring-2 "
        "focus:ring-stone-900/10"
    )
    class_input_err = (
        "w-full min-h-11 rounded-2xl border border-rose-300 bg-stone-50 "
        "px-4 py-3 text-sm text-stone-900 outline-none "
        "focus:border-rose-400 focus:bg-white focus:ring-2 "
        "focus:ring-rose-200"
    )
    class_pw_wrap = "relative"
    class_input_pw = "pr-16"
    class_reveal = (
        "absolute inset-y-1 right-1 min-h-0 cursor-pointer rounded-xl border-0 "
        "bg-transparent px-3 text-xs font-medium text-stone-500 hover:text-stone-900"
    )
    class_hint = "text-xs text-stone-400"
    class_hint_err = "text-xs text-rose-600"
    class_submit = (
        "mt-2 min-h-11 w-full cursor-pointer rounded-full border-0 "
        "bg-stone-800 px-5 py-3 text-sm font-semibold text-stone-50 "
        "hover:bg-stone-700 focus-visible:outline-none "
        "focus-visible:ring-2 focus-visible:ring-stone-900/20"
    )
    class_switch = "mt-6 mb-0 text-center text-sm text-stone-500"
    class_text_btn = (
        "min-h-0 cursor-pointer border-0 bg-transparent p-0 font-medium "
        "text-stone-900 underline underline-offset-2"
    )
    class_ok = "flex flex-col items-center text-center"
    class_mark = (
        "flex h-12 w-12 items-center justify-center rounded-full "
        "bg-emerald-50 text-xs font-semibold uppercase tracking-widest "
        "text-emerald-700"
    )
    class_out = (
        "mt-8 min-h-11 cursor-pointer rounded-full border border-stone-200 "
        "bg-white px-5 py-2.5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )

    mode = MorphState("login")
    show_password = MorphState(False)
    submitting = MorphState(False)
    authed = MorphState(False)
    error_stamp = MorphState("idle")

    email = RefState("")
    password = RefState("")
    name = RefState("")
    err_email = RefState("")
    err_password = RefState("")
    err_name = RefState("")
    err_form = RefState("")

    @staticmethod
    def Accept(message: str = "") -> AuthDecision:
        return AuthDecision(True, message)

    @staticmethod
    def Reject(message: str, *, blocked: bool = False) -> AuthDecision:
        return AuthDecision(False, message, blocked)

    def authenticate(self, *, email: str, password: str, name: str, signup: bool) -> AuthDecision:
        """Host seam. Validation has already passed.

        Demo: ``you@blocked.test`` is refused. Everything else that passed
        field checks is accepted. Replace with a real authenticator.
        """
        if email.lower().endswith("@blocked.test"):
            return self.Reject(
                "This account is not allowed to sign in.",
                blocked=True,
            )
        return self.Accept("Account created" if signup else "Signed in")

    def render(self):
        if bool(self.authed):
            return self._render_success()
        return self._render_card()

    def _render_success(self):
        email = str(self.email or "")
        return div(
            div(
                span("In", className=self.class_mark),
                h1("You're in", className=self.class_title + " mt-4"),
                p(
                    f"Signed in as {email}" if email else "Session started.",
                    className=self.class_lede,
                ),
                button(
                    "Sign out",
                    type="button",
                    className=self.class_out,
                    **bind(self.logout),
                ),
                className=self.class_ok,
            ),
            id=self.id,
            className=self.class_card,
        )

    def _render_card(self):
        mode = str(self.mode or "login")
        is_signup = mode == "signup"
        show_pw = bool(self.show_password)
        busy = bool(self.submitting)

        title = "Create account" if is_signup else "Welcome back"
        subtitle = (
            "Join in under a minute. No spam, ever."
            if is_signup
            else "Sign in to continue to your workspace."
        )
        submit_label = (
            "Creating…" if (is_signup and busy)
            else "Signing in…" if busy
            else ("Create account" if is_signup else "Sign in")
        )

        kids = [
            div(
                h1(title, className=self.class_title),
                p(subtitle, className=self.class_lede),
                className=self.class_head,
            ),
            div(
                button(
                    "Sign in",
                    type="button",
                    className=self.class_tab_on if not is_signup else self.class_tab,
                    **bind(self.set_mode, mode="login"),
                ),
                button(
                    "Sign up",
                    type="button",
                    className=self.class_tab_on if is_signup else self.class_tab,
                    **bind(self.set_mode, mode="signup"),
                ),
                className=self.class_tabs,
                role="tablist",
            ),
        ]

        form_err = str(self.err_form or "")
        if form_err:
            kids.append(div(
                span(form_err, className=self.class_alert_text),
                className=self.class_alert,
                role="alert",
            ))

        fields = []
        if is_signup:
            fields.append(self._field(
                "name", "Full name", "text",
                str(self.name or ""), str(self.err_name or ""),
                placeholder="Ada Lovelace", autocomplete="name",
            ))
        fields.append(self._field(
            "email", "Email", "email",
            str(self.email or ""), str(self.err_email or ""),
            placeholder="you@company.com", autocomplete="email",
        ))
        fields.append(self._password_field(
            str(self.password or ""), str(self.err_password or ""),
            show_pw,
        ))

        kids.append(form(
            *fields,
            button(
                submit_label,
                type="button",
                className=self.class_submit,
                **bind(self.submit),
            ),
            id="login-form",
            className=self.class_form,
        ))

        if is_signup:
            kids.append(p(
                "Already have an account? ",
                button(
                    "Sign in",
                    type="button",
                    className=self.class_text_btn,
                    **bind(self.set_mode, mode="login"),
                ),
                className=self.class_switch,
            ))
        else:
            kids.append(p(
                "New here? ",
                button(
                    "Create an account",
                    type="button",
                    className=self.class_text_btn,
                    **bind(self.set_mode, mode="signup"),
                ),
                className=self.class_switch,
            ))

        return div(*kids, id=self.id, className=self.class_card)

    def _field(self, name, caption, input_type, value, error, *, placeholder="", autocomplete="off"):
        kids = [
            label(caption, className=self.class_label),
            input_(
                type=input_type,
                name=name,
                value=value,
                placeholder=placeholder,
                autocomplete=autocomplete,
                className=self.class_input_err if error else self.class_input,
                **bind(self.set_field, field=name),
            ),
        ]
        if error:
            kids.append(span(error, className=self.class_hint_err, role="alert"))
        return div(*kids, className=self.class_field)

    def _password_field(self, value, error, show):
        inp = (
            f"{self.class_input_err} {self.class_input_pw}"
            if error
            else f"{self.class_input} {self.class_input_pw}"
        )
        kids = [
            label("Password", className=self.class_label),
            div(
                input_(
                    type="text" if show else "password",
                    name="password",
                    id="login-password",
                    value=value,
                    placeholder="At least 8 characters",
                    autocomplete="current-password",
                    className=inp,
                    **bind(self.set_field, field="password"),
                ),
                button(
                    "Hide" if show else "Show",
                    type="button",
                    className=self.class_reveal,
                    **bind(self.toggle_password),
                ),
                className=self.class_pw_wrap,
            ),
        ]
        if error:
            kids.append(span(error, className=self.class_hint_err, role="alert"))
        if str(self.mode or "") == "signup" and not error:
            kids.append(span(
                "Use 8+ characters with at least one number.",
                className=self.class_hint,
            ))
        return div(*kids, className=self.class_field)

    def _tick_error(self):
        self.error_stamp = "b" if self.error_stamp == "a" else "a"

    def _clear_errors(self):
        self.err_email = self.err_password = self.err_name = self.err_form = ""

    def _take_fields(self, email: str = "", password: str = "", name: str = "", **kwargs):
        """Attach live form values onto RefState before a morph."""
        if email:
            self.email = str(email)
        elif kwargs.get("email") is not None:
            self.email = str(kwargs["email"])
        if password:
            self.password = str(password)
        elif kwargs.get("password") is not None:
            self.password = str(kwargs["password"])
        if name:
            self.name = str(name)
        elif kwargs.get("name") is not None:
            self.name = str(kwargs["name"])

    @action(caps=())
    def set_mode(self, mode: str = "login", email: str = "", password: str = "", name: str = ""):
        self._take_fields(email=email, password=password, name=name)
        self.mode = mode if mode in ("login", "signup") else "login"
        self._clear_errors()
        self.submitting = False
        return update_with(self)

    @action(caps=())
    def toggle_password(self, email: str = "", password: str = "", name: str = ""):
        self._take_fields(email=email, password=password, name=name)
        self.show_password = not bool(self.show_password)
        return update_with(self)

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, "")
        raw = "" if raw is None else str(raw)
        if field == "email":
            self.email, self.err_email = raw, ""
        elif field == "password":
            self.password, self.err_password = raw, ""
        elif field == "name":
            self.name, self.err_name = raw, ""
        else:
            return None
        self.err_form = ""
        return update_with(self)

    @action(caps=("auth.login", "auth.signup"))
    def submit(
        self,
        email: str = "",
        password: str = "",
        name: str = "",
        **kwargs,
    ):
        self._take_fields(email=email, password=password, name=name, **kwargs)
        self._clear_errors()
        is_signup = str(self.mode or "login") == "signup"
        email = str(self.email or "").strip()
        password = str(self.password or "")
        name = str(self.name or "").strip()

        ok = True
        if is_signup and len(name) < 2:
            self.err_name = "Enter your full name."
            ok = False
        if not _email_ok(email):
            self.err_email = "Enter a valid email address."
            ok = False
        if not _password_ok(password, signup=is_signup):
            self.err_password = (
                "Use 8+ characters with at least one number."
                if is_signup else "Password must be at least 8 characters."
            )
            ok = False

        if not ok:
            self._tick_error()
            return update_with(self, extra_ops=[notify("Check the highlighted fields")])

        decision = self.authenticate(
            email=email, password=password, name=name, signup=is_signup,
        )
        if not decision.ok:
            self.err_form = decision.message or "Sign-in was refused."
            self._tick_error()
            return update_with(
                self,
                extra_ops=[notify("Sign-in blocked" if decision.blocked else decision.message)],
            )

        self.authed = True
        self.password = ""
        self.show_password = False
        msg = decision.message or ("Account created" if is_signup else "Signed in")
        return update_with(self, extra_ops=[notify(msg)])

    @action(caps=())
    def logout(self):
        self.authed = False
        self.password = ""
        self._clear_errors()
        self.mode = "login"
        self.show_password = False
        return update_with(self, extra_ops=[notify("Signed out")])
