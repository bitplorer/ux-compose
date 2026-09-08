"""Drop-in command palette — query attaches before the morph.

Host seam: override ``COMMANDS`` and ``on_run(key)``. Opening is public.
Style: edit the ``class_*`` Tailwind strings. No companion CSS.

MorphState: ``open``, ``dirty``. RefState: ``query``. Caps: none.
A11y: ``role=dialog`` ``aria-modal`` labelledby; search ``role=combobox``.
Escape / scrim via OverlayChrome. Focus: panel tabindex + input autofocus.
"""

from __future__ import annotations

from ux_compose.kit.overlay import overlay as overlay_chrome

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
    form,
    h2,
    input_,
    label,
    li,
    p,
    span,
    ul,
)


class Command(Component):
    """Filter commands, then run one.

    ``COMMANDS`` is ``(key, label, hint)``. Query is RefState so typing
    survives the morph. Override ``on_run`` in the product.
    The resting card stays in flow; the palette is presence on top of it.
    """

    id = "command"

    class_card = (
        "[grid-area:card] self-start relative mx-auto flex w-full max-w-xl flex-col gap-4 rounded-3xl border "
        "border-stone-200 bg-white p-6 text-stone-900 shadow-sm"
    )
    class_kicker = "text-xs font-medium uppercase tracking-widest text-stone-400"
    class_title = "m-0 font-serif text-2xl font-semibold tracking-tight"
    class_lede = "m-0 text-sm leading-relaxed text-stone-500"
    class_btn_primary = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border-0 bg-stone-800 px-5 text-sm font-medium text-stone-50 hover:bg-stone-700"
    )
    class_btn_ghost = (
        "inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full "
        "border border-stone-200 bg-white px-5 text-sm font-medium text-stone-900 "
        "hover:bg-stone-100"
    )
    class_input = (
        "min-h-11 w-full rounded-2xl border border-stone-200 bg-stone-50 "
        "px-4 py-3 text-sm text-stone-900 outline-none focus:border-stone-400 "
        "focus:bg-white focus:ring-2 focus:ring-stone-900/10"
    )
    class_scrim = "fixed inset-0 z-40 cursor-pointer border-0 bg-stone-900/40"
    class_panel = (
        "fixed left-1/2 top-[16%] z-50 flex w-[min(32rem,calc(100vw-2rem))] "
        "-translate-x-1/2 flex-col gap-3 rounded-3xl bg-white px-5 py-5 shadow-xl"
    )
    class_form = "flex flex-col gap-2"
    class_list = "m-0 flex max-h-64 list-none flex-col overflow-auto p-0"
    class_row = (
        "flex min-h-11 w-full cursor-pointer items-center justify-between "
        "gap-4 rounded-xl border-0 bg-transparent px-3 text-left "
        "text-inherit hover:bg-stone-100"
    )
    class_hint = "text-xs uppercase tracking-widest text-stone-400"
    class_sr = "sr-only"

    COMMANDS = (
        ("go-desk", "Open the desk", "Session"),
        ("go-work", "Jump to work", "Nav"),
        ("push-toast", "Push a notice", "Ops"),
        ("open-filters", "Open filters", "Catalog"),
        ("sign-out", "Sign out", "Session"),
    )

    open = MorphState(False)
    query = RefState("")
    dirty = MorphState("idle")

    def on_run(self, key: str) -> str:
        """Host seam. Return toast copy. Demo stand-in echoes the key."""
        return key.replace("-", " ")

    def _commands(self):
        return tuple(self.COMMANDS)

    def _hits(self):
        q = str(self.query or "").strip().lower()
        rows = self._commands()
        if not q:
            return rows
        return tuple(
            row
            for row in rows
            if q in row[0].lower() or q in row[1].lower() or q in row[2].lower()
        )

    def _mark_dirty(self):
        self.dirty = "b" if self.dirty == "a" else "a"

    def _chrome(self):
        return overlay_chrome(self.id, kind="dialog")

    def _resting(self):
        return [
            span("Jump", className=self.class_kicker),
            h2("Command palette", className=self.class_title),
            p("Type to filter. Run is public chrome.", className=self.class_lede),
            button(
                "Open palette",
                type="button",
                className=self.class_btn_primary,
                **bind(self.open_pal),
            ),
        ]

    def render(self):
        is_open = bool(self.open)
        q = str(self.query or "")
        kids = list(self._resting())
        if is_open:
            ch = self._chrome()
            hits = self._hits()
            list_id = f"{self.id}-list"
            title_id = f"{self.id}-title"
            rows = [
                li(
                    button(
                        span(label),
                        span(hint, className=self.class_hint),
                        type="button",
                        role="option",
                        className=self.class_row,
                        **bind(self.run, key=key),
                    ),
                    id=f"cmd-{key}",
                )
                for key, label, hint in hits[:7]
            ]
            listing = (
                ul(*rows, id=list_id, className=self.class_list, role="listbox")
                if rows
                else p(
                    f"No commands match “{q}”." if q else "No commands.",
                    id=list_id,
                    className=self.class_lede,
                    role="status",
                )
            )
            kids.extend([
                button(
                    span("Close", className=self.class_sr),
                    type="button",
                    id=ch.scrim_id,
                    className=self.class_scrim,
                    aria_label="Close",
                    data_channel_on=ch.dismiss_on(),
                    **bind(self.close),
                ),
                div(
                    span("Jump", className=self.class_kicker),
                    h2("Command palette", id=title_id, className=self.class_title),
                    form(
                        label("Filter commands", html_for=f"{self.id}-q", className=self.class_sr),
                        input_(
                            type="search",
                            name="q",
                            id=f"{self.id}-q",
                            value=q,
                            placeholder="Filter commands",
                            autocomplete="off",
                            autofocus=True,
                            className=self.class_input,
                            role="combobox",
                            aria_expanded="true",
                            aria_autocomplete="list",
                            aria_controls=list_id,
                            **bind(self.set_field, field="q"),
                        ),
                        button(
                            "Filter",
                            type="submit",
                            className=self.class_btn_ghost,
                            **bind(self.type_query),
                        ),
                        id="command-form",
                        className=self.class_form,
                    ),
                    listing,
                    button(
                        "Close",
                        type="button",
                        id=ch.dismiss_id,
                        className=self.class_btn_ghost,
                        data_channel_on=ch.dismiss_on(),
                        **bind(self.close),
                    ),
                    id=ch.panel_id,
                    className=self.class_panel,
                    role="dialog",
                    aria_modal="true",
                    aria_labelledby=title_id,
                    **ch.focus_attrs(),
                ),
            ])
        return div(
            *kids,
            id=self.id,
            className=self.class_card,
            data_open="1" if is_open else "0",
        )

    def _take_q(self, q: str = "", **kwargs):
        if q:
            self.query = str(q)
        elif kwargs.get("q") is not None:
            self.query = str(kwargs["q"])

    @action(caps=())
    def open_pal(self):
        self.open = True
        self.query = ""
        self._mark_dirty()
        return update_with(self, self._chrome().open_plan())

    @action(caps=())
    def close(self):
        self.open = False
        self.query = ""
        self._mark_dirty()
        return update_with(self)

    @action(caps=())
    def type_query(self, q: str = ""):
        self._take_q(q=q)
        self.open = True
        self._mark_dirty()
        return update_with(self)

    @action(caps=())
    def set_field(self, field: str = "", value: str = "", **kwargs):
        raw = value if value != "" else kwargs.get(field, kwargs.get("q", ""))
        if field in ("q", "query"):
            self.query = "" if raw is None else str(raw)
            self._mark_dirty()
            return update_with(self)
        return None

    @action(caps=())
    def run(self, key: str = "", q: str = ""):
        self._take_q(q=q)
        keys = {row[0] for row in self._commands()}
        if key not in keys:
            return update_with(self)
        msg = self.on_run(key)
        self.open = False
        self.query = ""
        self._mark_dirty()
        return update_with(self, extra_ops=[notify(msg)])
