"""Drop-in context menu — click or longpress on the same control.

Host seam: override ``ITEMS`` and ``on_run(key)``.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

Longpress lives on the *trigger*, not the host, so menu items do not inherit it.
The menu is a floating panel (list-none), not a native tab/list.
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


def _plan(name: str, target: str, *, ms: int = 120):
    try:
        from ux_compose import scene, rise

        if scene is None or rise is None:
            return None
        return scene(name).enter(target, rise.enter(ms=ms))
    except Exception:
        return None


class ContextMenu(Component):
    """Hold or click the canvas. Items are named keys."""

    id = "contextmenu"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_stage = "relative"
    class_canvas = (
        "flex min-h-40 w-full cursor-pointer flex-col items-center justify-center gap-1 "
        "rounded-2xl border border-dashed border-stone-300 bg-stone-50 px-4 text-center "
        "select-none"
    )
    class_menu = (
        "absolute left-1/2 top-1/2 z-30 m-0 flex w-56 list-none "
        "-translate-x-1/2 -translate-y-1/2 flex-col rounded-2xl "
        "border border-stone-200 bg-white p-1.5 shadow-xl"
    )
    class_item = "m-0 block list-none p-0"
    class_row = (
        "flex min-h-11 w-full cursor-pointer items-center rounded-xl border-0 "
        "bg-transparent px-3 text-left text-sm text-stone-900 hover:bg-stone-100 "
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-900/15"
    )
    class_scrim = "fixed inset-0 z-20 cursor-pointer border-0 bg-transparent"
    class_choice = "m-0 text-sm text-stone-500"
    class_sr = "sr-only"

    ITEMS = (
        ("rename", "Rename"),
        ("duplicate", "Duplicate"),
        ("inspect", "Inspect"),
    )

    open = MorphState(False)
    ran = RefState("")
    dirty = MorphState("idle")

    def on_run(self, key: str) -> str:
        return key.replace("-", " ")

    def _mark_dirty(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def render(self):
        if HAS_DOM and div is not None:
            return self._render_tree()
        return self._render_html()

    def _render_tree(self):
        is_open = bool(self.open)
        ran = str(self.ran or "")
        layer = []
        if is_open:
            rows = [
                li(
                    button(
                        label,
                        type="button",
                        role="menuitem",
                        className=self.class_row,
                        **bind(self.run, key=key),
                    ),
                    className=self.class_item,
                )
                for key, label in self.ITEMS
            ]
            layer = [
                button(
                    span("Close", className=self.class_sr),
                    type="button",
                    className=self.class_scrim,
                    aria_label="Close menu",
                    **bind(self.close),
                ),
                ul(*rows, className=self.class_menu, role="menu"),
            ]
        return div(
            span("Hold or click", className=self.class_kicker),
            h2("Context menu", className=self.class_title),
            p(
                "The trigger accepts both pointers. Items stay on click only.",
                className=self.class_lede,
            ),
            p(f"Ran · {ran}" if ran else "No command yet.", className=self.class_choice),
            div(
                button(
                    span("Hold · or click", className="text-sm font-medium text-stone-700"),
                    span("Opens the same menu.", className="text-xs text-stone-400"),
                    type="button",
                    className=self.class_canvas,
                    data_channel_on="click longpress delay:480",
                    **bind(self.open_menu),
                ),
                *layer,
                className=self.class_stage,
            ),
            id=self.id,
            className=self.class_card,
            role="region",
            data_open="1" if is_open else "0",
            data_channel_id=self.id,
        )

    def _render_html(self):
        is_open = bool(self.open)
        ran = str(self.ran or "")
        choice = f"Ran · {html_escape(ran)}" if ran else "No command yet."
        open_menu = html_attrs(bind(self.open_menu))
        layer = []
        if is_open:
            rows = []
            for key, label in self.ITEMS:
                stamp = html_attrs(bind(self.run, key=key))
                rows.append(
                    f'<li class="{self.class_item}">'
                    f'<button type="button" role="menuitem" class="{self.class_row}" {stamp}>'
                    f"{html_escape(label)}</button></li>"
                )
            close = html_attrs(bind(self.close))
            layer.append(
                f'<button type="button" class="{self.class_scrim}" '
                f'aria-label="Close menu" {close}>'
                f'<span class="{self.class_sr}">Close</span></button>'
            )
            layer.append(
                f'<ul class="{self.class_menu}" role="menu">{"".join(rows)}</ul>'
            )
        return (
            f'<div id="{html_escape(self.id)}" class="{self.class_card}" role="region" '
            f'data-open="{"1" if is_open else "0"}" data-channel-id="{html_escape(self.id)}">'
            f'<span class="{self.class_kicker}">Hold or click</span>'
            f'<h2 class="{self.class_title}">Context menu</h2>'
            f'<p class="{self.class_lede}">The trigger accepts both pointers. Items stay on click only.</p>'
            f'<p class="{self.class_choice}">{choice}</p>'
            f'<div class="{self.class_stage}">'
            f'<button type="button" class="{self.class_canvas}" '
            f'data-channel-on="click longpress delay:480" {open_menu}>'
            f'<span class="text-sm font-medium text-stone-700">Hold · or click</span>'
            f'<span class="text-xs text-stone-400">Opens the same menu.</span>'
            f"</button>"
            f"{''.join(layer)}"
            f"</div></div>"
        )

    @action(caps=())
    def open_menu(self):
        self.open = True
        self._mark_dirty()
        return update_with(self, _plan("ctx-open", f"#{self.id}"))

    @action(caps=())
    def close(self):
        self.open = False
        self._mark_dirty()
        return update_with(self)

    @action(caps=())
    def run(self, key: str = ""):
        keys = {row[0] for row in self.ITEMS}
        if key not in keys:
            return update_with(self)
        self.ran = key
        self.open = False
        self._mark_dirty()
        return update_with(self, extra_ops=[notify(self.on_run(key))])
