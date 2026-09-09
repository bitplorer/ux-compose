"""Drop-in questionnaire — named questions as fieldset radiogroups.

Host seam: render slots OR subclass.
Accepted: ``questions`` (same type as the matching class const / attr); ``shell`` (bool; ``False`` renders only the interactive unit, no demo kicker/title/lede card).
Instance attrs win over class consts.
Choosing is public. Submit spends ``form.submit``.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``done``, ``dirty``. RefState: ``answers`` (tuple of pairs).
Caps: ``form.submit``. A11y: each question is ``fieldset`` + ``legend``;
options ``role=radiogroup`` / ``radio`` ``aria-checked``. Label↔id on
the group via legend id. Not FormLayout (free text) and not Fieldset
(one group).
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
    fieldset,
    h2,
    legend,
    p,
    span,
)


class Questionnaire(Component):
    """A short ask. Answers are named keys on RefState.

    ``QUESTIONS`` is ``(key, prompt, ((opt_key, opt_label), …))``.
    """

    id = "questionnaire"
    _SEAMS = {'questions': 'QUESTIONS'}

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_set = "m-0 flex flex-col gap-2 rounded-2xl border border-stone-200 p-4"
    class_legend = "px-1 text-sm font-medium"
    class_opt = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-transparent "
        "px-3 text-left text-sm hover:bg-stone-50"
    )
    class_opt_on = (
        "flex min-h-11 cursor-pointer items-center rounded-xl border-0 bg-stone-100 "
        "px-3 text-left text-sm font-medium"
    )
    class_btn = (
        "min-h-11 w-full cursor-pointer rounded-full border-0 bg-stone-800 px-5 "
        "text-sm font-semibold text-stone-50 hover:bg-stone-700"
    )

    QUESTIONS = (
        (
            "fit",
            "How should it fit?",
            (("ease", "With ease"), ("close", "Close")),
        ),
        (
            "when",
            "When do you need it?",
            (("now", "This week"), ("later", "Winter")),
        ),
    )

    answers = RefState(())
    done = MorphState(False)
    dirty = MorphState("idle")

    def on_submit(self, answers: dict[str, str]) -> str:
        return "Noted"

    def _questions(self):
        return tuple(self.QUESTIONS)

    def _map(self) -> dict[str, str]:
        raw = self.answers or ()
        if isinstance(raw, dict):
            return {str(k): str(v) for k, v in raw.items()}
        out: dict[str, str] = {}
        for item in raw:
            if isinstance(item, (tuple, list)) and len(item) >= 2:
                out[str(item[0])] = str(item[1])
        return out

    def _mark(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self, *, shell=None, **slots):
        apply_slots(self, seams=getattr(self, '_SEAMS', {}), shell=shell, **slots)
        answers = self._map()
        if bool(self.done):
            bits = ", ".join(f"{k}={v}" for k, v in answers.items()) or "empty"
            return kit_shell(self,
                p(bits, className=self.class_lede),
                id=self.id,
                className=self.class_card,
                data_done="1",
                chrome=(
                    span("Ask", className=self.class_kicker),
                    h2("Noted", className=self.class_title),
                ),
            )
        blocks = []
        for qkey, prompt, opts in self._questions():
            chosen = answers.get(qkey, "")
            legend_id = f"{self.id}-q-{qkey}"
            radios = [
                button(
                    lab,
                    type="button",
                    id=f"{self.id}-opt-{qkey}-{okey}",
                    role="radio",
                    aria_checked="true" if okey == chosen else "false",
                    className=self.class_opt_on if okey == chosen else self.class_opt,
                    **bind(self.choose, question=qkey, key=okey),
                )
                for okey, lab in opts
            ]
            blocks.append(
                fieldset(
                    legend(prompt, id=legend_id, className=self.class_legend),
                    div(
                        *radios,
                        role="radiogroup",
                        aria_labelledby=legend_id,
                        className="flex flex-col gap-1",
                    ),
                    className=self.class_set,
                )
            )
        card_attrs = {
            "id": self.id,
            "className": self.class_card,
            "data_done": "0",
        }
        for qkey, _prompt, _opts in self._questions():
            card_attrs[f"data_{qkey}"] = answers.get(qkey, "")
        return kit_shell(self,
            *blocks,
            button("Send answers", type="button", className=self.class_btn, **bind(self.submit)),
            **card_attrs,
            chrome=(
                span("Ask", className=self.class_kicker),
                h2("A few questions", className=self.class_title),
                p("Named answers. Submit spends form.submit.", className=self.class_lede),
            ),
        )

    @action(caps=())
    def choose(self, question: str = "", key: str = ""):
        allowed_q = {row[0]: {o[0] for o in row[2]} for row in self._questions()}
        if question not in allowed_q or key not in allowed_q[question]:
            return update_with(self)
        cur = self._map()
        cur[question] = key
        self.answers = tuple(sorted(cur.items()))
        self._mark()
        return update_with(self, extra_ops=[notify(f"{question}:{key}")])

    @action(caps=("form.submit",))
    def submit(self):
        self.done = True
        self._mark()
        return update_with(self, extra_ops=[notify(self.on_submit(self._map()))])
