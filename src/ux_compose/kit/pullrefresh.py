"""Drop-in pull-to-refresh — vertical swipe on the list, not a new attribute.

Host seam: override ``SEED`` and ``on_refresh()`` (returns extra rows).
Style: edit the ``class_*`` Tailwind strings. No companion CSS.
"""

from __future__ import annotations

from ux_compose import (
    HAS_DOM,
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
    li,
    p,
    span,
    ul,
)
from ux_compose.helpers import html_attrs, html_escape


def _plan(name: str, target: str, *, ms: int = 140):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene(name).enter(target, rise.enter(ms=ms))
    except Exception:
        return None


class PullRefresh(Component):
    """Swipe down the list (or tap Refresh). Phase is a name, never a spinner int.

    Host ``swipe.vertical``. The Refresh control accepts ``click swipe.down``
    so axis-lock + convention never invent a second attribute.
    """

    id = "pullrefresh"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_stage = (
        "flex min-h-56 flex-col gap-2 rounded-2xl border border-stone-200 bg-stone-50 "
        "px-3 py-3"
    )
    class_list = "m-0 flex list-none flex-col gap-1 p-0"
    class_row = (
        "rounded-xl border border-stone-200 bg-white px-3 py-3 text-sm text-stone-800"
    )
    class_hint = "m-0 text-center text-xs uppercase tracking-widest text-stone-400"
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_busy = "m-0 text-center text-sm text-stone-500"

    SEED = (
        "Reserved the throw.",
        "Oiled the oak board.",
        "Marked the work shirt.",
    )
    MORE = (
        "Folded the linen.",
        "Minted a Cap for checkout.",
        "Waxed the stool.",
        "Filed the clay lip.",
    )

    items = RefState(None)
    phase = MorphState("idle")  # idle | refreshing | caught
    dirty = MorphState("idle")
    _cursor = RefState(0)

    def on_refresh(self):
        """Host seam. Return extra lines. Demo walks MORE."""
        have = list(self.items or self.SEED)
        rest = [x for x in self.MORE if x not in have]
        take = rest[:1]
        return tuple(take + have)

    def _mark_dirty(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def _rows(self):
        rows = self.items
        if rows is None:
            return tuple(self.SEED)
        return tuple(rows)

    def render(self):
        if HAS_DOM and div is not None:
            return self._render_tree()
        return self._render_html()

    def _render_tree(self):
        phase = str(self.phase or "idle")
        rows = self._rows()
        lis = [
            li(x, className=self.class_row, id=f"pr-{i}") for i, x in enumerate(rows)
        ]
        hint = {
            "refreshing": "Fetching the table…",
            "caught": "Caught up.",
            "idle": "Swipe down · or tap Refresh",
        }.get(phase, "Swipe down · or tap Refresh")
        return div(
            span("Feed", className=self.class_kicker),
            h2("Pull to refresh", className=self.class_title),
            p(
                "Vertical swipe is a synthesizer. The Refresh control accepts swipe.down.",
                className=self.class_lede,
            ),
            div(
                p(hint, className=self.class_busy if phase == "refreshing" else self.class_hint),
                ul(*lis, className=self.class_list),
                className=self.class_stage,
                style="touch-action:pan-x;user-select:none;",
            ),
            button(
                "Refresh",
                type="button",
                className=self.class_btn_ghost,
                data_channel_on="click swipe.down",
                **bind(self.refresh),
            ),
            id=self.id,
            className=self.class_card,
            data_phase=phase,
            data_channel_on="swipe.vertical threshold:56",
        )

    def _render_html(self):
        phase = str(self.phase or "idle")
        rows = self._rows()
        lis = [
            f'<li class="{self.class_row}" id="pr-{i}">{html_escape(x)}</li>'
            for i, x in enumerate(rows)
        ]
        hint = {
            "refreshing": "Fetching the table…",
            "caught": "Caught up.",
            "idle": "Swipe down · or tap Refresh",
        }.get(phase, "Swipe down · or tap Refresh")
        hint_cls = self.class_busy if phase == "refreshing" else self.class_hint
        stamp = html_attrs(bind(self.refresh))
        return (
            f'<div id="{html_escape(self.id)}" class="{self.class_card}" '
            f'data-phase="{html_escape(phase)}" data-channel-on="swipe.vertical threshold:56">'
            f'<span class="{self.class_kicker}">Feed</span>'
            f'<h2 class="{self.class_title}">Pull to refresh</h2>'
            f'<p class="{self.class_lede}">Vertical swipe is a synthesizer. The Refresh control accepts swipe.down.</p>'
            f'<div class="{self.class_stage}" style="touch-action:pan-x;user-select:none;">'
            f'<p class="{hint_cls}">{html_escape(hint)}</p>'
            f'<ul class="{self.class_list}">{"".join(lis)}</ul>'
            f"</div>"
            f'<button type="button" class="{self.class_btn_ghost}" '
            f'data-channel-on="click swipe.down" {stamp}>Refresh</button>'
            f"</div>"
        )

    @action(caps=())
    def refresh(self):
        self.phase = "refreshing"
        self._mark_dirty()
        nxt = self.on_refresh()
        self.items = nxt
        self.phase = "caught" if set(self.MORE).issubset(set(nxt)) else "idle"
        self._mark_dirty()
        return update_with(
            self,
            _plan("pr-refresh", f"#{self.id}"),
            extra_ops=[notify("refreshed")],
        )
