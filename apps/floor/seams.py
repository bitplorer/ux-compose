"""Floor seams — kit subclasses that read and write the House.

Polish stays on ``ux_compose.kit``. This file owns data, not chrome.
"""

from __future__ import annotations

from ux_compose import MorphState, RefState, bind, button, h2, p, span
from ux_compose.kit import (
    Accordion,
    ActionSheet,
    Breadcrumb,
    Calendar,
    Carousel,
    Chips,
    Combobox,
    Command,
    ContextMenu,
    Dialog,
    Dropdown,
    Empty,
    Kanban,
    Kpi,
    Lightbox,
    Login,
    Otp,
    Pagination,
    Plans,
    Presence,
    Progress,
    PullRefresh,
    Rating,
    Select,
    Sheet,
    Sidebar,
    Skeleton,
    Slider,
    Stepper,
    Table,
    Tabs,
    Timeline,
    Toast,
    Typeahead,
    Wishlist,
)

from .host import HOUSE

_CHIP_ON = {
    "flax": "bg-[#e8dcc8] text-[#3d2914] ring-1 ring-[#c9b89a]",
    "walnut": "bg-[#c4a574] text-[#3d2914] ring-1 ring-[#8b6914]/40",
    "merino": "bg-[#d4c4b0] text-[#3d2914] ring-1 ring-[#9a8470]/40",
    "river": "bg-[#c9a882] text-[#3d2914] ring-1 ring-[#a67c52]/40",
    "quiet": "bg-stone-800 text-stone-50 ring-1 ring-stone-900",
    "winter": "bg-sky-100 text-sky-950 ring-1 ring-sky-200",
}

_DOT = {
    "flax": "bg-[#c9b89a]",
    "walnut": "bg-[#8b6914]",
    "merino": "bg-[#9a8470]",
    "river": "bg-[#a67c52]",
    "quiet": "bg-stone-400",
    "winter": "bg-sky-400",
}


class FloorRating(Rating):
    def on_rate(self, key: str) -> str:
        HOUSE.set_rating(key)
        return key


class FloorKanban(Kanban):
    cut = RefState(("flax-01", "river-04"))
    make = RefState(("walnut-02",))
    keep = RefState(("merino-03",))

    def _cards(self):
        return {row[0]: row for row in HOUSE.kanban_cards()}

    def _lanes(self):
        return HOUSE.kanban_lanes()

    def on_move(self, sku: str, to: str) -> str:
        HOUSE.move_piece(sku, to)
        return f"{sku} → {to}"

    def on_archive(self, sku: str) -> str:
        HOUSE.archive_piece(sku)
        return f"archived {sku}"


class FloorTimeline(Timeline):
    LANES = (
        ("all", "All"),
        ("cut", "Cut"),
        ("make", "Make"),
        ("keep", "Keep"),
    )
    events = RefState(())

    def _events(self):
        return tuple(self.events or HOUSE.events())


class FloorKpi(Kpi):
    bag = RefState(4)
    held = RefState(36)
    placed = RefState(1)

    def on_tick(self) -> str:
        HOUSE.sale()
        return "sale"

    def on_reset(self) -> str:
        HOUSE.zero()
        return "zeroed"


class FloorSlider(Slider):
    def on_set(self, n: int) -> str:
        HOUSE.set_pour(n)
        return f"{n}"


class FloorLightbox(Lightbox):
    slide = MorphState("flax")

    def _slides(self):
        return HOUSE.slides()

    def _wash(self, key: str) -> str:
        return HOUSE.wash(key)

    def _ink(self, key: str) -> str:
        return HOUSE.ink(key)

    def on_open(self, key: str) -> str:
        HOUSE.note("view", sku=key)
        return key


class FloorWishlist(Wishlist):
    ids = RefState(("flax", "merino"))
    WASH = {
        "flax": "bg-gradient-to-br from-[#e8dcc8] to-[#c9b89a]",
        "walnut": "bg-gradient-to-br from-[#c4a574] to-[#8b6914]",
        "merino": "bg-gradient-to-br from-[#d4c4b0] to-[#9a8470]",
        "river": "bg-gradient-to-br from-[#c9a882] to-[#a67c52]",
        "brass": "bg-gradient-to-br from-[#e6d28a] to-[#c4a035]",
    }

    def _items(self):
        return HOUSE.catalog_items()

    def on_toggle(self, sku: str, on: bool) -> str:
        HOUSE.toggle_saved(sku, on)
        return sku


class FloorProgress(Progress):
    def on_finish(self) -> str:
        HOUSE.note("pour-done")
        return "done"


class FloorEmpty(Empty):
    def on_ready(self) -> str:
        self.body = HOUSE.shelf
        HOUSE.note("shelf-ready")
        return "ready"


class FloorPresence(Presence):
    PEERS = HOUSE.peers
    peers = RefState(HOUSE.peers)

    def _peers(self):
        return tuple(self.peers or HOUSE.peers)

    def on_set(self, key: str) -> str:
        HOUSE.set_self(key)
        return key


class FloorChips(Chips):
    tags = RefState(("flax", "quiet"))
    SUGGESTIONS = HOUSE.materials()

    def _suggestions(self):
        return HOUSE.materials()

    def _chip_on(self, key: str) -> str:
        return _CHIP_ON.get(key, "bg-stone-200 text-stone-800 ring-1 ring-stone-300")

    def on_add(self, tag: str) -> str:
        HOUSE.add_tag(tag)
        return tag

    def on_remove(self, tag: str) -> str:
        HOUSE.remove_tag(tag)
        return tag


class FloorSkeleton(Skeleton):
    def on_arrive(self) -> str:
        self.body = HOUSE.shelf
        HOUSE.note("arrived")
        return "arrived"


class FloorLogin(Login):
    def authenticate(self, *, email: str, password: str, name: str, signup: bool):
        return HOUSE.authenticate(
            email=email, password=password, name=name, signup=signup
        )


class FloorOtp(Otp):
    def on_verify(self, code: str) -> str | None:
        return HOUSE.verify_otp(code)


class FloorTabs(Tabs):
    def _items(self):
        return HOUSE.tabs()


class FloorAccordion(Accordion):
    def _sections(self):
        return HOUSE.sections()


class FloorDropdown(Dropdown):
    value = MorphState("flax")

    def _options(self):
        return HOUSE.options()


class FloorDialog(Dialog):
    title = RefState("Archive the walnut mallet?")
    body = RefState("The Host will drop it from the board. This spends a Cap.")

    def _resting(self):
        return [
            span("Authority", className=self.class_kicker),
            h2("Confirm a delete", className=self.class_title),
            p("Asking is public. Confirming spends a Cap.", className=self.class_lede),
            button(
                "Archive the walnut mallet…",
                type="button",
                className=self.class_btn_danger,
                **bind(self.ask, id="walnut-02"),
            ),
        ]

    def on_confirm(self, target: str) -> str:
        if target:
            HOUSE.archive_piece(target)
        HOUSE.note("confirm", target=target)
        return f"Archived {target}" if target else "Archived"


class FloorSheet(Sheet):
    title = RefState("The walnut mallet")
    body = RefState("Oiled twice. The head is the work.")


class FloorToast(Toast):
    pass


class FloorCommand(Command):
    def _commands(self):
        return HOUSE.commands()

    def on_run(self, key: str) -> str:
        HOUSE.note("command", key=key)
        return key.replace("-", " ")


class FloorTable(Table):
    COLUMNS = (("name", "Piece"), ("stage", "Stage"), ("price", "Price"))

    def _rows(self):
        key = str(self.sort or "name")
        if bool(self.cleared):
            rows = list(self.items or ())
        else:
            live = tuple(self.items or ())
            rows = list(live if live else HOUSE.table_rows())

        def val(row):
            return str((row[1] or {}).get(key, ""))

        return tuple(sorted(rows, key=val))

    def on_archive(self, skus: tuple[str, ...]) -> str:
        for sku in skus:
            HOUSE.archive_piece(sku)
        n = len(skus)
        return f"Archived {n} piece" if n == 1 else f"Archived {n} pieces"


class FloorPagination(Pagination):
    def _pages(self):
        return HOUSE.pages()


class FloorCombobox(Combobox):
    def _options(self):
        return HOUSE.names()


class FloorSidebar(Sidebar):
    active = MorphState("desk")

    def _items(self):
        return HOUSE.sidebar()


class FloorBreadcrumb(Breadcrumb):
    here = MorphState("walnut")

    def _trail(self):
        return HOUSE.trail()


class FloorStepper(Stepper):
    STEPS = HOUSE.steps()
    step = MorphState("mark")

    def _steps(self):
        return HOUSE.steps()

    def on_finish(self) -> str:
        HOUSE.note("flow-done")
        return "Flow finished"


class FloorCarousel(Carousel):
    slide = MorphState("flax")

    def _slides(self):
        return HOUSE.slides()


class FloorCalendar(Calendar):
    def on_pick(self, day: str) -> str:
        HOUSE.day = day
        HOUSE.note("day", day=day)
        return day


class FloorSelect(Select):
    def _groups(self):
        return HOUSE.groups()


class FloorPlans(Plans):
    def _plans(self):
        return HOUSE.plans()

    def on_choose(self, key: str) -> str:
        HOUSE.plan = key
        HOUSE.note("plan", key=key)
        return key


class FloorActionSheet(ActionSheet):
    ACTIONS = HOUSE.actions()

    def on_pick(self, key: str) -> str:
        HOUSE.note("sheet-pick", key=key)
        return key.replace("-", " ")


class FloorContextMenu(ContextMenu):
    ITEMS = HOUSE.menu()

    def on_run(self, key: str) -> str:
        HOUSE.note("menu", key=key)
        return key.replace("-", " ")


class FloorTypeahead(Typeahead):
    OPTIONS = HOUSE.names()

    def on_pick(self, label: str) -> str:
        HOUSE.note("pick", label=label)
        return label


class FloorPullRefresh(PullRefresh):
    SEED = HOUSE.seed()
    MORE = HOUSE.more()

    def on_refresh(self):
        have = list(self.items or HOUSE.seed())
        rest = [x for x in HOUSE.more() if x not in have]
        take = rest[:1]
        HOUSE.note("refresh", added=take[0] if take else "")
        return tuple(take + have)


for _cls, _cid in (
    (FloorRating, "rating"),
    (FloorKanban, "kanban"),
    (FloorTimeline, "timeline"),
    (FloorKpi, "kpi"),
    (FloorSlider, "slider"),
    (FloorLightbox, "lightbox"),
    (FloorWishlist, "wishlist"),
    (FloorProgress, "progress"),
    (FloorEmpty, "empty"),
    (FloorPresence, "presence"),
    (FloorChips, "chips"),
    (FloorSkeleton, "skeleton"),
    (FloorLogin, "login"),
    (FloorOtp, "otp"),
    (FloorTabs, "tabs"),
    (FloorAccordion, "accordion"),
    (FloorDropdown, "dropdown"),
    (FloorDialog, "dialog"),
    (FloorSheet, "sheet"),
    (FloorToast, "toast"),
    (FloorCommand, "command"),
    (FloorTable, "table"),
    (FloorPagination, "pagination"),
    (FloorCombobox, "combobox"),
    (FloorSidebar, "sidebar"),
    (FloorStepper, "stepper"),
    (FloorCarousel, "carousel"),
    (FloorCalendar, "calendar"),
    (FloorSelect, "select"),
    (FloorPlans, "plans"),
    (FloorActionSheet, "actionsheet"),
    (FloorContextMenu, "contextmenu"),
    (FloorTypeahead, "typeahead"),
    (FloorPullRefresh, "pullrefresh"),
    (FloorBreadcrumb, "breadcrumb"),
):
    _cls.id = _cid


ALL = (
    FloorRating,
    FloorKanban,
    FloorTimeline,
    FloorKpi,
    FloorSlider,
    FloorLightbox,
    FloorWishlist,
    FloorProgress,
    FloorEmpty,
    FloorPresence,
    FloorChips,
    FloorSkeleton,
    FloorLogin,
    FloorOtp,
    FloorTabs,
    FloorAccordion,
    FloorDropdown,
    FloorDialog,
    FloorSheet,
    FloorToast,
    FloorCommand,
    FloorTable,
    FloorPagination,
    FloorCombobox,
    FloorSidebar,
    FloorBreadcrumb,
    FloorStepper,
    FloorCarousel,
    FloorCalendar,
    FloorSelect,
    FloorPlans,
    FloorActionSheet,
    FloorContextMenu,
    FloorTypeahead,
    FloorPullRefresh,
)


def hydrate(app) -> None:
    """Pull live magnitudes from the House onto registered units."""
    get = getattr(getattr(app, "behavior", None), "get", None)
    if get is None:
        return
    pairing = (
        ("wishlist", "ids", tuple(HOUSE.saved)),
        ("kanban", "cut", HOUSE.lane("cut")),
        ("kanban", "make", HOUSE.lane("make")),
        ("kanban", "keep", HOUSE.lane("keep")),
        ("kpi", "bag", HOUSE.bag),
        ("kpi", "held", HOUSE.held),
        ("kpi", "placed", HOUSE.placed),
        ("chips", "tags", tuple(HOUSE.tags)),
        ("timeline", "events", HOUSE.events()),
        ("presence", "peers", HOUSE.peers),
        ("slider", "value", HOUSE.pour),
        ("rating", "stars", HOUSE.rating),
        ("lightbox", "slide", "flax"),
        ("lightbox", "open", False),
        ("carousel", "slide", "flax"),
    )
    for cid, field, value in pairing:
        try:
            inst = get(cid)
        except Exception:
            continue
        if inst is None:
            continue
        setattr(inst, field, value)
