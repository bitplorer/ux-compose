"""Drop-in form layout — labeled fields with error wiring.

Host seam: render slots OR subclass.
Accepted: ``fields`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``dirty``. RefState: ``values``, ``errors``. Caps: ``form.submit``.
A11y: label ``html_for`` ↔ control ``id``; ``aria-invalid`` +
``aria-describedby`` on errors. Group is a ``form``.
"""

from __future__ import annotations

from ux_compose.component import Component
from ux_compose.kit_construct import apply_slots, kit_shell
from ux_compose import (
    MorphState,
    RefState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    form,
    h2,
    input_,
    label,
    p,
    span,
)


class FormLayout(Component):
    """Stacked labeled fields. Values attach before the morph."""

    id = "formlayout"
    _SEAMS = {'fields': 'FIELDS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_form = "flex flex-col gap-4"
    class_field = "flex flex-col gap-1.5"
    class_label = "text-sm font-medium"
    class_input = (
        "w-full min-h-11 rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 "
        "text-sm outline-none focus:border-stone-400 focus:bg-white"
    )
    class_input_err = (
        "w-full min-h-11 rounded-2xl border border-rose-300 bg-stone-50 px-4 py-3 "
        "text-sm outline-none focus:border-rose-400"
    )
    class_hint_err = "text-xs text-rose-600"
    class_submit = (
        "mt-1 min-h-11 cursor-pointer rounded-full border-0 bg-stone-800 px-5 "
        "text-sm font-semibold text-stone-50 hover:bg-stone-700"
    )

    FIELDS = (
        ("name", "Full name", "text", "Ada Lovelace"),
        ("email", "Email", "email", "ada@atelier.test"),
        ("note", "Note", "text", "For the winter catalog"),
    )

    values = RefState(())
    errors = RefState(())
    dirty = MorphState("idle")

    def on_submit(self, values: dict[str, str]) -> str:
        return "Saved"

    def _fields(self):
        return tuple(self.FIELDS)

    def _map(self, raw) -> dict[str, str]:
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}
        out = {}
        for row in raw or ():
            if isinstance(row, (tuple, list)) and len(row) == 2:
                out[str(row[0])] = str(row[1])
        return out

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        vals = self._map(self.values)
        errs = self._map(self.errors)
        fields = []
        for name, caption, kind, ph in self._fields():
            fid = f"{self.id}-{name}"
            err = errs.get(name, "")
            err_id = f"{fid}-err"
            fields.append(
                div(
                    label(caption, className=self.class_label, html_for=fid),
                    input_(
                        type=kind,
                        name=name,
                        id=fid,
                        value=vals.get(name, ""),
                        placeholder=ph,
                        className=self.class_input_err if err else self.class_input,
                        aria_invalid="true" if err else "false",
                        **({"aria_describedby": err_id} if err else {}),
                        **bind(self.set_field, field=name),
                    ),
                    span(err, id=err_id, className=self.class_hint_err, role="alert") if err else span("", className="sr-only"),
                    className=self.class_field,
                )
            )
        return kit_shell(self,
            form(
                *fields,
                button("Save", type="button", className=self.class_submit, **bind(self.submit)),
                className=self.class_form,
            ),
            id=self.id,
            className=self.class_card,
            chrome=(
                span("Form", className=self.class_kicker),
                h2("Write it down", className=self.class_title),
                p("Each label points at its control. Errors describe the field.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, "")
        vals = self._map(self.values)
        vals[field] = "" if raw is None else str(raw)
        errs = self._map(self.errors)
        errs.pop(field, None)
        self.values = tuple(vals.items())
        self.errors = tuple(errs.items())
        self._mark()
        return update_with(self)

    @action(caps=("form.submit",))
    def submit(self, **kwargs):
        vals = self._map(self.values)
        for name, caption, _k, _ph in self._fields():
            if kwargs.get(name):
                vals[name] = str(kwargs[name])
        errs = {}
        if len(vals.get("name", "").strip()) < 2:
            errs["name"] = "Enter a name."
        if "@" not in vals.get("email", ""):
            errs["email"] = "Enter a valid email."
        self.values = tuple(vals.items())
        self.errors = tuple(errs.items())
        self._mark()
        if errs:
            return update_with(self, extra_ops=[notify("Check the highlighted fields")])
        return update_with(self, extra_ops=[notify(self.on_submit(vals))])
