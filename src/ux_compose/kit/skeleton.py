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
        "[grid-area:card] self-start mx-auto flex w-full min-w-0 max-w-xl flex-col gap-6 "
        "overflow-x-hidden rounded-[1.85rem] border border-stone-900/[0.07] bg-[#fdfcf8] p-7 text-stone-900 "
        "shadow-[0_0_0_1px_rgba(22,21,19,0.03),0_1px_2px_rgba(22,21,19,0.04),0_28px_56px_-24px_rgba(22,21,19,0.2)] "
        "dark:border-white/10 dark:bg-[#141311] dark:text-stone-50 dark:shadow-none"
    )
    class_kicker = (
        "text-[0.6875rem] font-medium uppercase tracking-[0.22em] text-stone-400 "
        "dark:text-stone-500"
    )
    class_title = (
        "m-0 font-serif text-[1.85rem] font-semibold leading-[1.12] tracking-[-0.03em]"
    )
    class_lede = (
        "m-0 max-w-[36ch] text-[0.9375rem] leading-relaxed text-stone-500 "
        "dark:text-stone-400"
    )
    class_skel = "flex flex-col"
    class_bar = "mt-2.5 h-3 rounded-lg bg-stone-200/90 animate-pulse dark:bg-stone-800"
    class_bar_lg = (
        "h-36 w-full rounded-[1.15rem] bg-stone-200/90 animate-pulse dark:bg-stone-800"
    )
    class_hero = (
        "h-36 w-full rounded-[1.15rem] "
        "bg-gradient-to-br from-[#e8dcc8] via-[#c9b89a] to-[#8a7354]"
    )
    class_copy = "mt-4 flex flex-col gap-1.5"
    class_ready_title = (
        "m-0 font-serif text-[1.35rem] font-light tracking-[-0.02em] "
        "text-stone-800 dark:text-stone-100"
    )
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-900 px-5 text-sm font-medium text-stone-50 "
        "transition hover:bg-stone-800 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-white"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-transparent px-4 text-sm font-medium text-stone-500 "
        "transition hover:text-stone-800 active:scale-[0.98] "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15 "
        "dark:text-stone-400 dark:hover:text-stone-50"
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
                p(
                    "The gate is part of the design. It is not a blank stage.",
                    className=self.class_lede,
                ),
                div(
                    div("", className=self.class_bar_lg, id=f"{self.id}-hero"),
                    div("", className=f"{self.class_bar} mt-4 w-2/5", id=f"{self.id}-s1"),
                    div("", className=f"{self.class_bar} w-full", id=f"{self.id}-s2"),
                    div("", className=f"{self.class_bar} w-4/5", id=f"{self.id}-s3"),
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
            h2("Loading the table", className=self.class_title),
            div(
                div("", className=self.class_hero, aria_hidden="true"),
                div(
                    h2("The table is set", className=self.class_ready_title),
                    p(
                        str(self.body or "Four objects. Linen, oak, wool, clay."),
                        className=self.class_lede,
                    ),
                    id=f"{self.id}-copy",
                    className=self.class_copy,
                ),
                id=f"{self.id}-body",
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
