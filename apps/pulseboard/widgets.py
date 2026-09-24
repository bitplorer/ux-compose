"""Kit subclasses + atelier-taught companions for the Pulseboard desk.

Kit is the source of truth — copies stay subclasses. Kanban / presence /
watchlist / chips follow examples/ encodings (no kit stem for those).
Isolation: this module never imports ux_channel.
"""

from __future__ import annotations

from ux_compose import (
    Component,
    MorphState,
    RefState,
    action,
    bind,
    button,
    div,
    h2,
    li,
    mark_dirty,
    notify,
    p,
    span,
    ul,
    update_with,
)
from ux_compose.kit.avatar import Avatar
from ux_compose.kit.badge import Badge
from ux_compose.kit.emptystate import EmptyState
from ux_compose.kit.feed import Feed
from ux_compose.kit.progress import Progress
from ux_compose.kit.rating import Rating
from ux_compose.kit.skeleton import Skeleton
from ux_compose.kit.slider import Slider
from ux_compose.kit.stats import Stats
from ux_compose.kit.themeswitch import ThemeSwitch
from ux_compose.kit.timeline import Timeline

from apps.pulseboard import data
from apps.pulseboard.theme import (
    BTN,
    BTN_GHOST,
    KIT_BTN,
    KIT_CARD,
    KIT_KICKER,
    KIT_LEDE,
    KIT_TILE,
    KIT_TITLE,
    NUM,
)


class PulseKpis(Stats):
    """Six named magnitudes. Stats kit; extra tiles via ITEMS."""

    id = "desk_kpis"
    ITEMS = data.KPI_ITEMS
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_grid = "grid grid-cols-2 gap-3 min-[720px]:grid-cols-3"
    class_tile = KIT_TILE
    class_num = NUM
    class_btn = KIT_BTN
    class_unit = "flex w-full min-w-0 flex-col gap-4"

    def render(self, *, shell=None, **slots):
        from ux_compose.kit_construct import apply_slots

        apply_slots(self, seams=getattr(self, "_SEAMS", {}), shell=False, **slots)
        tiles = []
        for key, lab, val in self._items():
            delta = data.KPI_DELTAS.get(key, "")
            tiles.append(
                div(
                    span(lab, className=self.class_kicker),
                    p(val, className=self.class_num, aria_label=f"{lab} {val}"),
                    span(delta, className="text-xs font-medium text-teal-700 dark:text-teal-300") if delta else "",
                    className=self.class_tile,
                    role="group",
                    aria_label=lab,
                )
            )
        return div(
            span("Today", className=self.class_kicker),
            h2("The desk", className=self.class_title),
            p("Six named magnitudes. A sale rewrites RefState, then dirty morphs.", className=self.class_lede),
            div(*tiles, className=self.class_grid),
            div(
                button("A sale lands", type="button", className=self.class_btn, **bind(self.tick_up)),
                button("Restate", type="button", className=BTN_GHOST, **bind(self.refresh)),
                className="flex flex-wrap gap-2",
            ),
            id=self.id,
            className=KIT_CARD,
        )

    @action(caps=())
    def refresh(self):
        self.items = tuple(self.ITEMS)
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self, extra_ops=[notify("desk restated")])

    @action(caps=())
    def tick_up(self):
        """A sale lands — rewrite display strings, then dirty."""
        self.items = (
            ("mrr", "MRR", "$186.4k"),
            ("net", "Net new", "$15.0k"),
            ("churn", "Logo churn", "0.7%"),
            ("expand", "Expansion", "$10.1k"),
            ("seats", "Active seats", "1,271"),
            ("nps", "NPS", "64"),
        )
        self.dirty = "b" if self.dirty == "a" else "a"
        return update_with(self, extra_ops=[notify("a sale landed")])


class PulseTimeline(Timeline):
    id = "desk_timeline"
    LANES = data.TIMELINE_LANES
    EVENTS = data.TIMELINE_EVENTS
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_chips = "flex flex-wrap gap-1"
    class_chip = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border "
        "border-slate-200 bg-slate-50 px-3 text-xs font-medium "
        "dark:border-white/10 dark:bg-[#0c1017] dark:text-slate-300"
    )
    class_chip_on = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border-0 "
        "bg-slate-900 px-3 text-xs font-medium text-white dark:bg-teal-400 "
        "dark:text-slate-950"
    )
    class_list = (
        "m-0 flex list-none flex-col gap-3 border-l border-slate-200 p-0 pl-4 "
        "dark:border-white/10"
    )
    class_row = "relative text-sm"
    class_unit = "flex w-full min-w-0 flex-col gap-4"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseRating(Rating):
    id = "desk_rating"
    STARS = data.RATING_STARS
    value = MorphState("four")
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_star = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent text-lg text-slate-300"
    )
    class_star_on = (
        "inline-flex min-h-11 min-w-11 cursor-pointer items-center justify-center "
        "rounded-full border-0 bg-transparent text-lg text-amber-400"
    )
    class_unit = "flex w-full min-w-0 flex-col gap-3"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseProgress(Progress):
    id = "desk_progress"
    value = RefState(68)
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_bar = (
        "h-2.5 w-full overflow-hidden rounded-full bg-slate-100 "
        "dark:bg-[#0c1017] [&::-webkit-progress-bar]:bg-slate-100 "
        "[&::-webkit-progress-value]:bg-teal-500 dark:[&::-webkit-progress-bar]:bg-[#0c1017]"
    )
    class_btn = KIT_BTN
    class_unit = "flex w-full min-w-0 flex-col gap-3"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseSlider(Slider):
    id = "desk_horizon"
    value = RefState(90)
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_label = "text-sm font-medium"
    class_input = "w-full accent-teal-600"
    class_unit = "flex w-full min-w-0 flex-col gap-3"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseEmpty(EmptyState):
    id = "desk_empty"
    TITLE = "No saved views yet"
    BODY = "Pin a forecast slice. Opening this region is public — Caps stay off this control."
    ACTION = "Pin West desk"
    class_card = (
        KIT_CARD + " items-center border-dashed px-6 py-10 text-center"
    )
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE + " max-w-sm"
    class_btn = KIT_BTN
    class_unit = "flex w-full min-w-0 flex-col items-center gap-3 text-center"

    def on_act(self) -> str:
        return "West desk pinned"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseSkeleton(Skeleton):
    id = "desk_skeleton"
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_bar = "h-3 animate-pulse rounded-full bg-slate-200 dark:bg-white/10"
    class_btn = BTN_GHOST
    class_unit = "flex w-full min-w-0 flex-col gap-4"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseTheme(ThemeSwitch):
    id = "desk_theme"
    value = MorphState("dark")
    THEMES = (
        ("dark", "Ink", "Command night"),
        ("light", "Paper", "Gallery day"),
        ("system", "House", "Follow the room"),
    )
    class_card = "flex min-w-0 flex-col gap-2"
    class_kicker = KIT_KICKER
    class_title = "sr-only"
    class_lede = "sr-only"
    class_group = "flex flex-wrap gap-1"
    class_opt = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border "
        "border-slate-200 bg-white px-3 text-xs font-medium text-slate-600 "
        "dark:border-white/10 dark:bg-transparent dark:text-slate-300"
    )
    class_opt_on = (
        "inline-flex min-h-9 cursor-pointer items-center rounded-full border-0 "
        "bg-slate-900 px-3 text-xs font-medium text-white dark:bg-teal-400 "
        "dark:text-slate-950"
    )
    class_name = "text-xs font-medium"
    class_hint = "sr-only"
    class_unit = "flex min-w-0 flex-col gap-1"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseBadge(Badge):
    """Region filter chips — Badge kit, product keys."""

    id = "desk_chips"
    ITEMS = data.REGIONS
    value = MorphState("all")
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_row = "flex flex-wrap gap-2"
    class_chip = (
        "inline-flex min-h-8 cursor-pointer items-center rounded-full border "
        "border-slate-200 bg-slate-50 px-3 text-xs font-medium "
        "dark:border-white/10 dark:bg-[#0c1017] dark:text-slate-300"
    )
    class_chip_on = (
        "inline-flex min-h-8 cursor-pointer items-center rounded-full border-0 "
        "bg-slate-900 px-3 text-xs font-medium text-white dark:bg-teal-400 "
        "dark:text-slate-950"
    )
    class_unit = "flex w-full min-w-0 flex-col gap-3"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseFeed(Feed):
    id = "desk_feed"
    SEED = data.FEED_SEED
    MORE = data.FEED_MORE
    items = RefState(("Harbor · $48k cleared", "Lumen · legal ping", "Northwind · seat spike"))
    class_card = KIT_CARD
    class_kicker = KIT_KICKER
    class_title = KIT_TITLE
    class_lede = KIT_LEDE
    class_item = (
        "rounded-2xl bg-slate-50 px-4 py-3 dark:bg-[#0c1017]"
    )
    class_btn = BTN_GHOST
    class_unit = "flex w-full min-w-0 flex-col gap-3"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseAvatar(Avatar):
    id = "desk_avatar"
    name = RefState("Noor Vale")
    class_card = "flex items-center gap-3"
    class_kicker = "sr-only"
    class_title = "sr-only"
    class_lede = "sr-only"
    class_mark = (
        "flex h-10 w-10 items-center justify-center rounded-full bg-teal-700 "
        "text-sm font-semibold text-white dark:bg-teal-400 dark:text-slate-950"
    )
    class_btn = "sr-only"
    class_unit = "flex items-center gap-3"

    def render(self, *, shell=None, **slots):
        return super().render(shell=False, **slots)


class PulseKanban(Component):
    """Three RefState columns, one dirty — same encoding as examples/table_board."""

    id = "desk_kanban"
    qualify = RefState(data.DEALS_QUALIFY)
    negotiate = RefState(data.DEALS_NEGOTIATE)
    close = RefState(data.DEALS_CLOSE)
    dirty = MorphState("idle")
    COLS = ("qualify", "negotiate", "close")
    LABELS = {"qualify": "Qualify", "negotiate": "Negotiate", "close": "Close"}

    def _col(self, name: str) -> list[str]:
        return list(getattr(self, name) or ())

    def render(self):
        cols = []
        for col in self.COLS:
            cards = []
            for sku in self._col(col):
                title, meta, region = data.KANBAN_META.get(sku, (sku, "", ""))
                nxt = self.COLS[(self.COLS.index(col) + 1) % 3]
                cards.append(
                    li(
                        span(title, className="m-0 text-sm font-medium"),
                        span(meta, className="text-xs text-slate-500 dark:text-slate-400"),
                        span(region, className=KIT_KICKER),
                        button(
                            f"To {self.LABELS[nxt]}",
                            type="button",
                            className=BTN_GHOST + " mt-2 min-h-9 text-xs",
                            **bind(self.move, sku=sku, to=nxt),
                        ),
                        id=f"deal-{sku}",
                        className=(
                            "flex flex-col gap-1 rounded-xl border border-slate-200 "
                            "bg-white px-3 py-3 dark:border-white/10 dark:bg-[#0c1017]"
                        ),
                    )
                )
            cols.append(
                div(
                    div(
                        h2(self.LABELS[col], className="m-0 text-sm font-semibold"),
                        span(str(len(self._col(col))), className=KIT_KICKER),
                        className="flex items-center justify-between px-0.5",
                    ),
                    ul(*cards, className="m-0 flex list-none flex-col gap-2 p-0"),
                    className="min-w-0 flex-1",
                )
            )
        return div(
            span("Pipeline", className=KIT_KICKER),
            h2("This week's paper", className=KIT_TITLE),
            p("Named columns. Cards keep id=deal-{sku} so presence survives the morph.", className=KIT_LEDE),
            div(*cols, className="grid gap-3 min-[860px]:grid-cols-3"),
            id=self.id,
            className=KIT_CARD,
            data_dirty=str(self.dirty or "idle"),
        )

    @action(caps=())
    def move(self, sku: str = "", to: str = "negotiate"):
        if to not in self.COLS:
            return update_with(self)
        for col in self.COLS:
            setattr(self, col, tuple(x for x in self._col(col) if x != sku))
        setattr(self, to, tuple(self._col(to) + [sku]))
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(f"{sku} → {to}")])


class PulsePresence(Component):
    """Self named · peers silent — examples/ops Presence encoding."""

    id = "desk_presence"
    self_state = MorphState("here")
    peers = RefState(data.PEERS)
    dirty = MorphState("idle")

    def render(self):
        me = str(self.self_state or "here")
        chips = [
            li(
                x,
                className=(
                    "inline-flex min-h-8 items-center rounded-full border "
                    "border-slate-200 bg-slate-50 px-3 text-xs "
                    "dark:border-white/10 dark:bg-[#0c1017] dark:text-slate-300"
                ),
            )
            for x in (self.peers or ())
        ]
        return div(
            span("Floor", className=KIT_KICKER),
            div(
                span("You", className="text-sm font-medium"),
                span(
                    me,
                    className=(
                        "inline-flex min-h-7 items-center rounded-full px-2.5 text-xs font-medium "
                        + (
                            "bg-emerald-500/15 text-emerald-700 dark:text-emerald-300"
                            if me == "here"
                            else "bg-slate-200 text-slate-600 dark:bg-white/10 dark:text-slate-300"
                        )
                    ),
                ),
                className="flex items-center gap-2",
            ),
            ul(*chips, className="m-0 flex list-none flex-wrap gap-1.5 p-0", role="list"),
            div(
                button(
                    "Here",
                    type="button",
                    className=KIT_BTN if me == "here" else BTN_GHOST,
                    **bind(self.set, key="here"),
                ),
                button(
                    "Away",
                    type="button",
                    className=KIT_BTN if me == "away" else BTN_GHOST,
                    **bind(self.set, key="away"),
                ),
                className="flex flex-wrap gap-2",
            ),
            id=self.id,
            className=KIT_CARD,
        )

    @action(caps=())
    def set(self, key: str = "here"):
        self.self_state = key if key in {"here", "away"} else "here"
        return update_with(self, extra_ops=[notify(str(self.self_state))])


class PulseWatchlist(Component):
    """Wishlist encoding — ids in RefState + dirty; heart is public."""

    id = "desk_watch"
    ids = RefState(("harbor", "kepler"))
    dirty = MorphState("idle")

    def render(self):
        held = set(self.ids or ())
        rows = []
        for sku, title in data.WATCHLIST:
            on = sku in held
            rows.append(
                li(
                    span(title, className="text-sm"),
                    button(
                        "Saved" if on else "Watch",
                        type="button",
                        className=KIT_BTN if on else BTN_GHOST,
                        **bind(self.toggle, sku=sku),
                    ),
                    id=f"watch-{sku}",
                    className="flex items-center justify-between gap-3",
                )
            )
        return div(
            span("Watchlist", className=KIT_KICKER),
            h2("Pinned paper", className=KIT_TITLE),
            p("Membership is RefState. The heart is public.", className=KIT_LEDE),
            ul(*rows, className="m-0 flex list-none flex-col gap-3 p-0"),
            id=self.id,
            className=KIT_CARD,
        )

    @action(caps=())
    def toggle(self, sku: str = ""):
        cur = list(self.ids or ())
        if sku in cur:
            cur = [x for x in cur if x != sku]
        elif sku:
            cur.append(sku)
        self.ids = tuple(cur)
        mark_dirty(self)
        return update_with(self, extra_ops=[notify(sku)])


class PulseClose(Component):
    """Quarter close spends a Cap. Wipe is refused unless the host mints."""

    id = "desk_close"
    closed = MorphState(False)
    refused = MorphState(False)

    def render(self):
        closed = bool(self.closed)
        refused = bool(self.refused)
        status = "Quarter sealed." if closed else (
            "Refused — no Cap." if refused else "Close spends quarter.close. Wipe is fail-closed without a mint."
        )
        return div(
            span("Authority", className=KIT_KICKER),
            h2("Close the quarter", className=KIT_TITLE),
            p(status, className=KIT_LEDE, role="status"),
            div(
                button(
                    "Close quarter",
                    type="button",
                    className=BTN,
                    **bind(self.close_quarter),
                ),
                button(
                    "Wipe board",
                    type="button",
                    className=BTN_GHOST,
                    **bind(self.wipe),
                ),
                className="flex flex-wrap gap-2",
            ),
            id=self.id,
            className=KIT_CARD,
            data_closed="1" if closed else "0",
        )

    @action(caps=("quarter.close",))
    def close_quarter(self):
        self.closed = True
        self.refused = False
        return update_with(self, extra_ops=[notify("quarter sealed")])

    @action(caps=("admin.reset",))
    def wipe(self):
        self.closed = False
        self.refused = False
        return update_with(self, extra_ops=[notify("board wiped")])

    @action(caps=())
    def mark_refused(self, reason: str = "no Cap"):
        self.refused = True
        return update_with(self, extra_ops=[notify(reason)])


BOARD_CLASSES: tuple[type, ...] = (
    PulseKpis,
    PulseTimeline,
    PulseRating,
    PulseProgress,
    PulseSlider,
    PulseEmpty,
    PulseSkeleton,
    PulseTheme,
    PulseBadge,
    PulseFeed,
    PulseAvatar,
    PulseKanban,
    PulsePresence,
    PulseWatchlist,
    PulseClose,
)
