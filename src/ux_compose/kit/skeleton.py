"""Drop-in skeleton / loading — loading MorphState.

Host seam: override ``on_arrive()``. Arrive / reload are public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

Empty, loading, ready are part of the design. Pulse bars keep stable ids
so a later stagger can address them without rewrite.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
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


def _arrive_plan(cid: str = "skeleton"):
    try:
        from ux_compose import scene, fade, rise

        if scene is None or fade is None or rise is None:
            return None
        return (
            scene("skeleton-arrive")
            .enter(f"#{cid}-body", fade.enter(ms=80))
            .enter(f"#{cid}-copy", rise.enter(ms=160))
        )
    except Exception:
        return None


class Skeleton(Component):
    """Loading gate. ``loading`` is qualitative MorphState. Body is silent.

    Pulse is CSS (``animate-pulse``). Motion recipes are additive on arrive.
    """

    id = "skeleton"

    class_card = (
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-5 "
        "overflow-x-hidden rounded-[1.75rem] border border-stone-200/90 bg-white p-6 text-stone-900 "
        "shadow-[0_1px_0_rgba(22,21,19,0.04),0_24px_48px_-28px_rgba(22,21,19,0.4)] "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-xs font-medium uppercase tracking-[0.2em] text-stone-500 "
        "dark:text-stone-400"
    )
    class_title = "m-0 font-serif text-3xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-600 dark:text-stone-400"
    class_skel = "flex flex-col gap-3"
    class_bar = "h-3 rounded-full bg-stone-200 animate-pulse dark:bg-stone-800"
    class_bar_lg = (
        "h-24 rounded-2xl bg-stone-200 animate-pulse dark:bg-stone-800"
    )
    class_copy = "flex flex-col gap-2"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 "
        "hover:bg-stone-700 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-200 dark:text-stone-900 dark:hover:bg-white"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:border-stone-700 dark:bg-stone-950 dark:text-stone-50 dark:hover:bg-stone-900"
    )

    loading = MorphState(True)
    body = RefState("")

    def on_arrive(self) -> str:
        return "arrived"

    def render(self):
        if bool(self.loading):
            return div(
                span("Gate", className=self.class_kicker),
                h2("Loading the table", className=self.class_title),
                p("The gate is part of the design. It is not a blank stage.", className=self.class_lede),
                div(
                    div("", className=self.class_bar_lg, id=f"{self.id}-hero"),
                    div("", className=f"{self.class_bar} w-2/3", id=f"{self.id}-s1"),
                    div("", className=f"{self.class_bar} w-full", id=f"{self.id}-s2"),
                    div("", className=f"{self.class_bar} w-1/2", id=f"{self.id}-s3"),
                    id=f"{self.id}-body",
                    className=self.class_skel,
                    aria_busy="true",
                    aria_label="Loading",
                ),
                button(
                    "Data arrives",
                    type="button",
                    className=self.class_btn_primary,
                    **bind(self.arrive),
                ),
                id=self.id,
                className=self.class_card,
                data_loading="1",
            )
        return div(
            span("Gate", className=self.class_kicker),
            div(
                h2("The table is set", className=self.class_title),
                p(
                    str(self.body or "Four objects. Linen, oak, wool, clay."),
                    className=self.class_lede,
                ),
                id=f"{self.id}-copy",
                className=self.class_copy,
            ),
            button(
                "Reload",
                type="button",
                className=self.class_btn_ghost,
                **bind(self.reload),
            ),
            id=self.id,
            className=self.class_card,
            data_loading="0",
        )

    @action(caps=())
    def arrive(self):
        self.loading = False
        self.body = "Quiet pieces for a working house."
        return update_with(
            self,
            _arrive_plan(self.id),
            extra_ops=[notify(self.on_arrive())],
        )

    @action(caps=())
    def reload(self):
        self.loading = True
        self.body = ""
        return update_with(self, extra_ops=[notify("loading")])
