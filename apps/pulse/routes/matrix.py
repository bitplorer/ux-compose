"""Page unit: matrix.py → Matrix — specialist happy-path room.

One Pulse surface that exercises the compose→channel tree:
bind + @action Ops, Document fragment extract, Cap mint / deny,
and morph-then-fade/rise/slide after Result.
"""
from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    action,
    bind,
    button,
    control,
    div,
    h1,
    h3,
    notify,
    optional_fade,
    optional_plan,
    optional_slide,
    p,
    section,
    span,
    update_with,
)


class Matrix(Component):
    id = "matrix"
    tick = MorphState(0)
    stage = MorphState("idle")

    def render(self):
        n = int(self.tick or 0)
        return section(
            span(
                "feature matrix · bind · Cap · morph-then-play",
                className="inline-flex rounded-full border border-emerald-500/30 px-3 py-1 text-xs font-mono text-emerald-700 dark:text-emerald-400",
            ),
            h1(
                "Specialist matrix",
                className="mt-6 font-serif text-4xl font-medium tracking-tight",
            ),
            p(
                "One Pulse room for the compose→channel happy paths. "
                "Clock A GET is Document HTML. Clock B is /ux-channel/action.",
                className="mt-3 max-w-xl text-sm text-stone-600 dark:text-stone-400",
            ),
            div(
                h3("Stage", className="font-serif text-lg"),
                p(
                    f"tick={n} · stage={self.stage}",
                    className="mt-1 font-mono text-xs text-stone-500",
                    id="matrix-readout",
                ),
                div(
                    button(
                        "Bind tick",
                        type="button",
                        className="rounded-full bg-stone-900 px-4 py-2 text-sm text-stone-50 dark:bg-stone-100 dark:text-stone-900",
                        **bind(self.tick_once),
                    ),
                    button(
                        "Fade",
                        type="button",
                        className="rounded-full border px-4 py-2 text-sm",
                        **control("matrix.play_fade"),
                    ),
                    button(
                        "Rise",
                        type="button",
                        className="rounded-full border px-4 py-2 text-sm",
                        **control("matrix.play_rise"),
                    ),
                    button(
                        "Slide",
                        type="button",
                        className="rounded-full border px-4 py-2 text-sm",
                        **control("matrix.play_slide"),
                    ),
                    button(
                        "Gated",
                        type="button",
                        className="rounded-full border px-4 py-2 text-sm",
                        **control("matrix.gated"),
                    ),
                    className="mt-4 flex flex-wrap gap-2",
                ),
                className=(
                    "mt-8 rounded-2xl border border-stone-200 bg-white p-6 "
                    "dark:border-stone-700 dark:bg-stone-900"
                ),
                id="matrix-stage",
            ),
            id=self.id,
            className="mx-auto max-w-5xl px-4 py-10",
        )

    @action(caps=())
    def tick_once(self):
        self.tick = int(self.tick or 0) + 1
        return update_with(self, extra_ops=[notify(f"tick={self.tick}")])

    @action(caps=())
    def play_fade(self):
        self.stage = "fade"
        return update_with(self, optional_fade("matrix-fade", "#matrix-stage"))

    @action(caps=())
    def play_rise(self):
        self.stage = "rise"
        return update_with(self, optional_plan("matrix-rise", "#matrix-stage"))

    @action(caps=())
    def play_slide(self):
        self.stage = "slide"
        return update_with(self, optional_slide("matrix-slide", "#matrix-stage"))

    @action(caps=("matrix.gated",))
    def gated(self):
        self.stage = "gated"
        return update_with(self, extra_ops=[notify("gated ok")])
