"""Page unit: settings.py → Settings — doctor + progressive capabilities."""
from __future__ import annotations

from ux_compose import Component, MorphState, action, control, update_with, doctor

try:
    from ux_compose import div, span, h1, h3, p, button, section, article, ul, li, HAS_DOM
except Exception:
    HAS_DOM = False
    div = span = h1 = h3 = p = button = section = article = ul = li = None  # type: ignore


class Settings(Component):
    id = "settings"
    refresh_tick = MorphState(0)

    def render(self):
        report = doctor([], fail=False)
        caps = report.capabilities or {}
        if not (HAS_DOM and div is not None):
            return f'<section id="settings">L{report.level_available}</section>'

        rows = [
            li(
                span(k, className="font-mono text-sm"),
                span(
                    "on" if v else "off",
                    className="rounded-full border px-2 py-0.5 text-xs font-mono " + (
                        "border-emerald-500/40 text-emerald-700" if v else "text-stone-500"
                    ),
                ),
                className="flex items-center justify-between gap-3 border-b border-stone-200 py-2 dark:border-stone-700",
            )
            for k, v in caps.items()
        ]
        teaching = [
            li(t, className="border-b border-stone-200 py-2 text-sm text-stone-600 dark:border-stone-700 dark:text-stone-400")
            for t in (report.teaching or [])[:4]
        ]
        return section(
            div(
                div(
                    h1("Settings & doctor", className="font-serif text-3xl tracking-tight"),
                    p("Progressive capabilities · Isolation · page-unit evidence", className="text-sm text-stone-500"),
                ),
                button(
                    f"Refresh · {int(self.refresh_tick or 0)}",
                    type="button",
                    className="rounded-full border px-4 py-2 text-sm",
                    **control("settings.refresh"),
                ),
                className="flex flex-wrap items-start justify-between gap-4",
            ),
            div(
                article(
                    h3("Capabilities", className="font-serif text-lg"),
                    p("Detected specialists at runtime", className="text-xs text-stone-500"),
                    ul(*rows, className="mt-3"),
                    p(f"doctor level L{report.level_available} · ok={report.ok}", className="mt-3 rounded-full border px-2 py-0.5 text-xs font-mono inline-block"),
                    className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-stone-700 dark:bg-stone-900",
                ),
                article(
                    h3("Teaching", className="font-serif text-lg"),
                    ul(*teaching, className="mt-3") if teaching else p("Full stack available", className="mt-3 text-sm text-stone-500"),
                    className="rounded-2xl border border-stone-200 bg-white p-6 dark:border-stone-700 dark:bg-stone-900",
                ),
                className="mt-8 grid gap-4 lg:grid-cols-2",
            ),
            id=self.id,
            className="mx-auto max-w-5xl px-4 py-10",
        )

    @action(caps=())
    def refresh(self):
        self.refresh_tick = int(self.refresh_tick or 0) + 1
        return update_with(self)
