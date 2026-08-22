"""Page unit: home.py → Home — Document trees + Tailwind className."""
from __future__ import annotations

from ux_compose import Component, MorphState, action, control, notify, update_with

try:
    from ux_compose import div, span, h1, p, a, button, section, article, HAS_DOM
except Exception:
    HAS_DOM = False
    div = span = h1 = p = a = button = section = article = None  # type: ignore


class Home(Component):
    id = "home"
    pulse = MorphState(0)
    greeting = MorphState("Welcome")

    def render(self):
        n = int(self.pulse or 0)
        attrs = control("home.beat")
        if not (HAS_DOM and div is not None):
            return f'<section id="home"><p>{self.greeting} · pulse {n}</p></section>'

        return section(
            span(
                "page unit · stem match · App.mount",
                className="inline-flex rounded-full border border-emerald-500/30 px-3 py-1 text-xs font-mono text-emerald-700 dark:text-emerald-400",
            ),
            h1(
                f"{self.greeting} to ",
                span("Pulse", className="text-amber-700 dark:text-amber-400"),
                className="mt-6 max-w-[14ch] font-serif text-5xl font-medium tracking-tight text-stone-900 dark:text-stone-100",
            ),
            p(
                "Document trees · Tailwind className · semantic control() · "
                "channel when live · HTMX opt-in only.",
                className="mt-4 max-w-xl text-lg text-stone-600 dark:text-stone-400",
            ),
            div(
                button(
                    f"Pulse · {n}",
                    type="button",
                    className="rounded-full bg-stone-900 px-4 py-2 text-sm font-medium text-stone-50 hover:bg-stone-800 dark:bg-stone-100 dark:text-stone-900",
                    **attrs,
                ),
                a(
                    "Open shop",
                    href="/shop",
                    className="rounded-full border border-stone-300 px-4 py-2 text-sm dark:border-stone-600",
                ),
                a(
                    "Interactive lab",
                    href="/lab",
                    className="rounded-full px-4 py-2 text-sm text-stone-600 dark:text-stone-400",
                ),
                className="mt-8 flex flex-wrap gap-3",
            ),
            div(
                article(
                    h1("Path law", className="font-serif text-xl"),
                    p(
                        "URL = filesystem only. Class name never in the path.",
                        className="mt-2 text-sm text-stone-600 dark:text-stone-400",
                    ),
                    className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm dark:border-stone-700 dark:bg-stone-900",
                ),
                article(
                    h1("Page unit", className="font-serif text-xl"),
                    p(
                        "Stem match picks the owner. Ambiguity fails closed.",
                        className="mt-2 text-sm text-stone-600 dark:text-stone-400",
                    ),
                    className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm dark:border-stone-700 dark:bg-stone-900",
                ),
                article(
                    h1("Progressive", className="font-serif text-xl"),
                    p(
                        "Write at L1. Unlock channel later — zero rewrite.",
                        className="mt-2 text-sm text-stone-600 dark:text-stone-400",
                    ),
                    className="rounded-2xl border border-stone-200 bg-white p-6 shadow-sm dark:border-stone-700 dark:bg-stone-900",
                ),
                className="mt-10 grid gap-4 sm:grid-cols-3",
            ),
            id=self.id,
            className="mx-auto max-w-5xl px-4 py-12",
        )

    @action(caps=())
    def beat(self):
        self.pulse = int(self.pulse or 0) + 1
        self.greeting = "Still here" if self.pulse > 3 else "Welcome"
        return update_with(self, extra_ops=[notify(f"pulse={self.pulse}")])
