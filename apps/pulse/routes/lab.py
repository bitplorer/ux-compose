"""Page unit: lab.py → Lab — tabs, counter, form, toast (tag trees)."""
from __future__ import annotations

from ux_compose import Component, MorphState, RefState, action, control, notify, update_with

try:
    from ux_compose import div, span, h1, h3, p, button, section, HAS_DOM
except Exception:
    HAS_DOM = False
    div = span = h1 = h3 = p = button = section = None  # type: ignore


class Lab(Component):
    id = "lab"
    tab = MorphState("counter")
    count = RefState(0)
    stamp = MorphState("idle")
    name = RefState("")
    email = RefState("")
    note = RefState("")
    valid = MorphState("idle")
    toast = RefState("")

    def render(self):
        if not (HAS_DOM and div is not None):
            return f'<section id="lab">lab tab={self.tab}</section>'

        tabs = []
        for key, label in (("counter", "Counter"), ("form", "Form"), ("toast", "Toast")):
            selected = self.tab == key
            tabs.append(
                button(
                    label, type="button",
                    className="rounded-full border px-3 py-1.5 text-sm " + (
                        "border-stone-400 bg-stone-100 dark:bg-stone-800" if selected else "border-transparent text-stone-500"
                    ),
                    **{"aria-selected": "true" if selected else "false"},
                    **control("lab.set_tab", tab=key),
                )
            )

        if self.tab == "counter":
            body = div(
                h3("RefState magnitude + Morph stamp", className="font-serif text-lg"),
                p(str(int(self.count or 0)), className="mt-4 font-serif text-5xl tracking-tight"),
                p(f"stamp={self.stamp}", className="mt-1 font-mono text-xs text-stone-500"),
                div(
                    button("\u2212", type="button", className="rounded-full border px-3 py-1.5", **control("lab.dec")),
                    button("+", type="button", className="rounded-full bg-stone-900 px-3 py-1.5 text-stone-50", **control("lab.inc")),
                    button("Reset", type="button", className="rounded-full px-3 py-1.5 text-sm", **control("lab.reset")),
                    className="mt-4 flex gap-2",
                ),
                className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-stone-700 dark:bg-stone-900",
            )
        elif self.tab == "form":
            body = div(
                h3("Validated form", className="font-serif text-lg"),
                p(f"name={self.name or '\u2014'} \u00b7 email={self.email or '\u2014'}", className="mt-2 text-sm text-stone-600"),
                div(
                    button("Save sample", type="button", className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50",
                           **control("lab.save_form", name="Ada", email="ada@example.com")),
                    span(str(self.valid), className="rounded-full border px-2 py-0.5 text-xs font-mono"),
                    className="mt-4 flex items-center gap-2",
                ),
                className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-stone-700 dark:bg-stone-900",
            )
        else:
            toast = div(str(self.toast), className="fixed bottom-4 right-4 z-40 rounded-xl border bg-white px-4 py-3 shadow-lg", id="toast") if self.toast else None
            body = div(
                h3("Toast plane", className="font-serif text-lg"),
                p("One-shot messages via notify + local toast state.", className="mt-1 text-sm text-stone-500"),
                div(
                    button("Show toast", type="button", className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50", **control("lab.show_toast")),
                    button("Dismiss", type="button", className="rounded-full px-4 py-2 text-sm", **control("lab.hide_toast")),
                    className="mt-4 flex gap-2",
                ),
                className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-stone-700 dark:bg-stone-900",
            )
            if toast is not None:
                body = div(body, toast)

        return section(
            h1("Interactive lab", className="font-serif text-3xl tracking-tight"),
            p("Tabs \u00b7 counter \u00b7 form \u00b7 toast \u2014 same Component, progressive-safe.", className="text-sm text-stone-500"),
            div(*tabs, className="mt-6 flex flex-wrap gap-2"),
            div(body, className="mt-4"),
            id=self.id,
            className="mx-auto max-w-5xl px-4 py-10",
        )

    @action(caps=())
    def set_tab(self, tab: str = "counter"):
        if tab in ("counter", "form", "toast"):
            self.tab = tab
        return update_with(self)

    @action(caps=())
    def inc(self):
        self.count = int(self.count or 0) + 1
        self.stamp = "a" if self.stamp == "b" else "b"
        return update_with(self)

    @action(caps=())
    def dec(self):
        self.count = max(0, int(self.count or 0) - 1)
        self.stamp = "a" if self.stamp == "b" else "b"
        return update_with(self)

    @action(caps=())
    def reset(self):
        self.count = 0
        self.stamp = "idle"
        return update_with(self, extra_ops=[notify("reset")])

    @action(caps=())
    def save_form(self, name: str = "", email: str = "", note: str = ""):
        if name:
            self.name = name
        if email:
            self.email = email
        if note:
            self.note = note
        ok = bool(self.name) and ("@" in str(self.email or ""))
        self.valid = "ok" if ok else "err"
        return update_with(self, extra_ops=[notify("Saved" if ok else "Name + valid email required")])

    @action(caps=())
    def show_toast(self):
        self.toast = "Pulse lab \u00b7 toast plane active"
        return update_with(self, extra_ops=[notify(self.toast)])

    @action(caps=())
    def hide_toast(self):
        self.toast = ""
        return update_with(self)
