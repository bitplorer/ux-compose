"""Drop-in stepper — named steps, public next, Cap on finish.

Host seam: override ``STEPS`` and ``on_finish()``.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    action,
    bind,
    notify,
    update_with,
    button,
    div,
    h2,
    p,
    span,
)


class Stepper(Component):
    """Wizard. Current step is a name, never an int MorphState.

    ``STEPS`` is ``(key, label, body)``. Finish spends ``flow.finish``.
    """

    id = "stepper"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full min-w-0 max-w-xl flex-col gap-5 overflow-x-hidden "
        "rounded-3xl border border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_row = "flex min-w-0 flex-wrap items-center justify-center gap-0"
    class_dot = (
        "flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border border-stone-200 bg-white text-xs font-semibold "
        "text-stone-500"
    )
    class_dot_on = (
        "flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-stone-800 text-xs font-semibold text-stone-50"
    )
    class_dot_done = (
        "flex h-11 w-11 shrink-0 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-stone-200 text-xs font-semibold text-stone-700"
    )
    class_line = "h-px min-w-4 flex-1 bg-stone-200"
    class_panel = "flex flex-col gap-2 rounded-2xl bg-stone-50 px-5 py-5"
    class_actions = "flex min-w-0 flex-wrap items-center justify-between gap-2"
    class_btn_primary = (
        "inline-flex min-h-11 shrink-0 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 shrink-0 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_ok = "flex flex-col items-center gap-2 py-6 text-center"
    class_mark = (
        "flex h-12 w-12 items-center justify-center rounded-full bg-emerald-50 "
        "text-xs font-semibold uppercase tracking-widest text-emerald-700"
    )

    STEPS = (
        ("account", "Account", "Name and email stay on this unit. Next is public."),
        ("plan", "Plan", "Pick a desk. Caps stay off chrome until the last step."),
        ("review", "Review", "Confirm the trail. Finish spends a Cap."),
    )

    step = MorphState("account")
    done = MorphState(False)

    def on_finish(self) -> str:
        """Host seam. Return the toast copy after the Cap spent."""
        return "Flow finished"

    def _steps(self):
        return tuple(self.STEPS)

    def _index(self):
        keys = [row[0] for row in self._steps()]
        cur = str(self.step or keys[0])
        if cur not in keys:
            cur = keys[0]
        return keys.index(cur), cur, keys

    def render(self):
        if bool(self.done):
            return div(
                div(
                    span("Done", className=self.class_mark),
                    h2("You're through", className=self.class_title),
                    p("The Cap was spent. Start again when you like.", className=self.class_lede),
                    button(
                        "Start again",
                        type="button",
                        className=self.class_btn_ghost + " mt-4",
                        **bind(self.reset),
                    ),
                    className=self.class_ok,
                ),
                id=self.id,
                className=self.class_card,
                data_done="1",
            )
        idx, cur, keys = self._index()
        rows = self._steps()
        key, label, body = rows[idx]
        dots = []
        for i, (k, lab, _b) in enumerate(rows):
            if i:
                dots.append(span("", className=self.class_line))
            cls = self.class_dot_on if i == idx else self.class_dot_done if i < idx else self.class_dot
            dots.append(
                button(
                    str(i + 1),
                    type="button",
                    title=lab,
                    className=cls,
                    **bind(self.goto, key=k),
                )
            )
        at_end = idx >= len(keys) - 1
        at_start = idx == 0
        primary = (
            button(
                "Finish",
                type="button",
                className=self.class_btn_primary,
                **bind(self.finish),
            )
            if at_end
            else button(
                "Continue",
                type="button",
                className=self.class_btn_primary,
                **bind(self.next),
            )
        )
        return div(
            span("Flow", className=self.class_kicker),
            div(*dots, className=self.class_row, aria_label="Steps"),
            div(
                span(f"Step {idx + 1} of {len(keys)}", className=self.class_kicker),
                h2(label, className=self.class_title),
                p(body, className=self.class_lede),
                className=self.class_panel,
            ),
            div(
                button(
                    "Back",
                    type="button",
                    className=self.class_btn_ghost,
                    **bind(self.prev),
                )
                if not at_start
                else span("", className="min-h-11"),
                primary,
                className=self.class_actions,
            ),
            id=self.id,
            className=self.class_card,
            data_step=cur,
        )

    @action(caps=())
    def goto(self, key: str = ""):
        keys = {row[0] for row in self._steps()}
        self.step = key if key in keys else self._steps()[0][0]
        self.done = False
        return update_with(self)

    @action(caps=())
    def next(self):
        idx, _cur, keys = self._index()
        if idx < len(keys) - 1:
            self.step = keys[idx + 1]
        return update_with(self)

    @action(caps=())
    def prev(self):
        idx, _cur, keys = self._index()
        if idx > 0:
            self.step = keys[idx - 1]
        return update_with(self)

    @action(caps=("flow.finish",))
    def finish(self):
        self.done = True
        return update_with(self, extra_ops=[notify(self.on_finish())])

    @action(caps=())
    def reset(self):
        self.done = False
        self.step = self._steps()[0][0]
        return update_with(self)
