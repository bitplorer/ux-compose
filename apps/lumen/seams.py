"""Lumen seams — kit subclasses that read and write the Press.

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

from .host import PRESS

_CHIP_ON = {
    "folio": "bg-[#e8dcc8] text-[#3d2914] ring-1 ring-[#c9b89a]",
    "punch": "bg-[#8a8680] text-[#1c1b19] ring-1 ring-[#4a4744]/40",
    "wick": "bg-[#d4c4b0] text-[#3d2914] ring-1 ring-[#9a8470]/40",
    "slip": "bg-[#c9a882] text-[#3d2914] ring-1 ring-[#a67c52]/40",
    "quiet": "bg-stone-800 text-stone-50 ring-1 ring-stone-900",
    "winter": "bg-sky-100 text-sky-950 ring-1 ring-sky-200",
}

_DOT = {
    "folio": "bg-[#c9b89a]",
    "punch": "bg-[#4a4744]",
    "wick": "bg-[#9a8470]",
    "slip": "bg-[#a67c52]",
    "quiet": "bg-stone-400",
    "winter": "bg-sky-400",
}


class LumenRating(Rating):
    def on_rate(self, key: str) -> str:
        PRESS.set_rating(key)
        return key


class LumenKanban(Kanban):
    cut = RefState(("folio-01", "slip-04"))
    make = RefState(("punch-02",))
    keep = RefState(("wick-03",))

    def _cards(self):
        return {row[0]: row for row in PRESS.kanban_cards()}

    def _lanes(self):
        return PRESS.kanban_lanes()

    def on_move(self, sku: str, to: str) -> str:
        PRESS.move_piece(sku, to)
        return f"{sku} → {to}"

    def on_archive(self, sku: str) -> str:
        PRESS.archive_piece(sku)
        return f"archived {sku}"


class LumenTimeline(Timeline):
    LANES = (
        ("all", "All"),
        ("cut", "Cut"),
        ("make", "Make"),
        ("keep", "Keep"),
    )
    events = RefState(())

    def _events(self):
        return tuple(self.events or PRESS.events())


class LumenKpi(Kpi):
    bag = RefState(4)
    held = RefState(36)
    placed = RefState(1)

    def on_tick(self) -> str:
        PRESS.sale()
        return "sale"

    def on_reset(self) -> str:
        PRESS.zero()
        return "zeroed"


class LumenSlider(Slider):
    def on_set(self, n: int) -> str:
        PRESS.set_pour(n)
        return f"{n}"


class LumenLightbox(Lightbox):
    slide = MorphState("folio")

    def _slides(self):
        return PRESS.slides()

    def _wash(self, key: str) -> str:
        return PRESS.wash(key)

    def _ink(self, key: str) -> str:
        return PRESS.ink(key)

    def on_open(self, key: str) -> str:
        PRESS.note("view", sku=key)
        return key


class LumenWishlist(Wishlist):
    ids = RefState(("folio", "wick"))
    WASH = {
        "folio": "bg-gradient-to-br from-[#e8dcc8] to-[#c9b89a]",
        "punch": "bg-gradient-to-br from-[#8a8680] to-[#4a4744]",
        "wick": "bg-gradient-to-br from-[#d4c4b0] to-[#9a8470]",
        "slip": "bg-gradient-to-br from-[#c9a882] to-[#a67c52]",
        "quoin": "bg-gradient-to-br from-[#e6d28a] to-[#c4a035]",
    }

    def _items(self):
        return PRESS.catalog_items()

    def on_toggle(self, sku: str, on: bool) -> str:
        PRESS.toggle_saved(sku, on)
        return sku


class LumenProgress(Progress):
    def on_finish(self) -> str:
        PRESS.note("pour-done")
        return "done"


class LumenEmpty(Empty):
    def on_ready(self) -> str:
        self.body = PRESS.shelf
        PRESS.note("shelf-ready")
        return "ready"


class LumenPresence(Presence):
    PEERS = PRESS.peers
    peers = RefState(PRESS.peers)

    def _peers(self):
        return tuple(self.peers or PRESS.peers)

    def on_set(self, key: str) -> str:
        PRESS.set_self(key)
        return key


class LumenChips(Chips):
    tags = RefState(("folio", "quiet"))
    SUGGESTIONS = PRESS.materials()

    def _suggestions(self):
        return PRESS.materials()

    def _chip_on(self, key: str) -> str:
        return _CHIP_ON.get(key, "bg-stone-200 text-stone-800 ring-1 ring-stone-300")

    def on_add(self, tag: str) -> str:
        PRESS.add_tag(tag)
        return tag

    def on_remove(self, tag: str) -> str:
        PRESS.remove_tag(tag)
        return tag


class LumenSkeleton(Skeleton):
    def on_arrive(self) -> str:
        self.body = PRESS.shelf
        PRESS.note("arrived")
        return "arrived"


class LumenLogin(Login):
    def authenticate(self, *, email: str, password: str, name: str, signup: bool):
        return PRESS.authenticate(
            email=email, password=password, name=name, signup=signup
        )


class LumenOtp(Otp):
    def on_verify(self, code: str) -> str | None:
        return PRESS.verify_otp(code)


class LumenTabs(Tabs):
    def _items(self):
        return PRESS.tabs()


class LumenAccordion(Accordion):
    def _sections(self):
        return PRESS.sections()


class LumenDropdown(Dropdown):
    value = MorphState("folio")

    def _options(self):
        return PRESS.options()


class LumenDialog(Dialog):
    title = RefState("Archive the steel punch?")
    body = RefState("The Host will drop it from the chase. This spends a Cap.")

    def _resting(self):
        return [
            span("Authority", className=self.class_kicker),
            h2("Confirm a delete", className=self.class_title),
            p("Asking is public. Confirming spends a Cap.", className=self.class_lede),
            button(
                "Archive the steel punch…",
                type="button",
                className=self.class_btn_danger,
                **bind(self.ask, id="punch-02"),
            ),
        ]

    def on_confirm(self, target: str) -> str:
        if target:
            PRESS.archive_piece(target)
        PRESS.note("confirm", target=target)
        return f"Archived {target}" if target else "Archived"


class LumenSheet(Sheet):
    title = RefState("The steel punch")
    body = RefState("The counter is the work. Strike once.")


class LumenToast(Toast):
    pass


class LumenCommand(Command):
    def _commands(self):
        return PRESS.commands()

    def on_run(self, key: str) -> str:
        PRESS.note("command", key=key)
        return key.replace("-", " ")


class LumenTable(Table):
    COLUMNS = (("name", "Piece"), ("stage", "Stage"), ("price", "Price"))

    def _rows(self):
        key = str(self.sort or "name")
        if bool(self.cleared):
            rows = list(self.items or ())
        else:
            live = tuple(self.items or ())
            rows = list(live if live else PRESS.table_rows())

        def val(row):
            return str((row[1] or {}).get(key, ""))

        return tuple(sorted(rows, key=val))

    def on_archive(self, skus: tuple[str, ...]) -> str:
        for sku in skus:
            PRESS.archive_piece(sku)
        n = len(skus)
        return f"Archived {n} piece" if n == 1 else f"Archived {n} pieces"


class LumenPagination(Pagination):
    def _pages(self):
        return PRESS.pages()


class LumenCombobox(Combobox):
    def _options(self):
        return PRESS.names()


class LumenSidebar(Sidebar):
    active = MorphState("desk")

    def _items(self):
        return PRESS.sidebar()


class LumenBreadcrumb(Breadcrumb):
    here = MorphState("punch")

    def _trail(self):
        return PRESS.trail()


class LumenStepper(Stepper):
    STEPS = PRESS.steps()
    step = MorphState("mark")

    def _steps(self):
        return PRESS.steps()

    def on_finish(self) -> str:
        PRESS.note("flow-done")
        return "Flow finished"


class LumenCarousel(Carousel):
    slide = MorphState("folio")

    def _slides(self):
        return PRESS.slides()


class LumenCalendar(Calendar):
    def on_pick(self, day: str) -> str:
        PRESS.day = day
        PRESS.note("day", day=day)
        return day


class LumenSelect(Select):
    def _groups(self):
        return PRESS.groups()


class LumenPlans(Plans):
    def _plans(self):
        return PRESS.plans()

    def on_choose(self, key: str) -> str:
        PRESS.plan = key
        PRESS.note("plan", key=key)
        return key


class LumenActionSheet(ActionSheet):
    ACTIONS = PRESS.actions()

    def on_pick(self, key: str) -> str:
        PRESS.note("sheet-pick", key=key)
        return key.replace("-", " ")


class LumenContextMenu(ContextMenu):
    ITEMS = PRESS.menu()

    def on_run(self, key: str) -> str:
        PRESS.note("menu", key=key)
        return key.replace("-", " ")


class LumenTypeahead(Typeahead):
    OPTIONS = PRESS.names()

    def on_pick(self, label: str) -> str:
        PRESS.note("pick", label=label)
        return label


class LumenPullRefresh(PullRefresh):
    SEED = PRESS.seed()
    MORE = PRESS.more()

    def on_refresh(self):
        have = list(self.items or PRESS.seed())
        rest = [x for x in PRESS.more() if x not in have]
        take = rest[:1]
        PRESS.note("refresh", added=take[0] if take else "")
        return tuple(take + have)


for _cls, _cid in (
    (LumenRating, "rating"),
    (LumenKanban, "kanban"),
    (LumenTimeline, "timeline"),
    (LumenKpi, "kpi"),
    (LumenSlider, "slider"),
    (LumenLightbox, "lightbox"),
    (LumenWishlist, "wishlist"),
    (LumenProgress, "progress"),
    (LumenEmpty, "empty"),
    (LumenPresence, "presence"),
    (LumenChips, "chips"),
    (LumenSkeleton, "skeleton"),
    (LumenLogin, "login"),
    (LumenOtp, "otp"),
    (LumenTabs, "tabs"),
    (LumenAccordion, "accordion"),
    (LumenDropdown, "dropdown"),
    (LumenDialog, "dialog"),
    (LumenSheet, "sheet"),
    (LumenToast, "toast"),
    (LumenCommand, "command"),
    (LumenTable, "table"),
    (LumenPagination, "pagination"),
    (LumenCombobox, "combobox"),
    (LumenSidebar, "sidebar"),
    (LumenStepper, "stepper"),
    (LumenCarousel, "carousel"),
    (LumenCalendar, "calendar"),
    (LumenSelect, "select"),
    (LumenPlans, "plans"),
    (LumenActionSheet, "actionsheet"),
    (LumenContextMenu, "contextmenu"),
    (LumenTypeahead, "typeahead"),
    (LumenPullRefresh, "pullrefresh"),
    (LumenBreadcrumb, "breadcrumb"),
):
    _cls.id = _cid


ALL = (
    LumenRating,
    LumenKanban,
    LumenTimeline,
    LumenKpi,
    LumenSlider,
    LumenLightbox,
    LumenWishlist,
    LumenProgress,
    LumenEmpty,
    LumenPresence,
    LumenChips,
    LumenSkeleton,
    LumenLogin,
    LumenOtp,
    LumenTabs,
    LumenAccordion,
    LumenDropdown,
    LumenDialog,
    LumenSheet,
    LumenToast,
    LumenCommand,
    LumenTable,
    LumenPagination,
    LumenCombobox,
    LumenSidebar,
    LumenBreadcrumb,
    LumenStepper,
    LumenCarousel,
    LumenCalendar,
    LumenSelect,
    LumenPlans,
    LumenActionSheet,
    LumenContextMenu,
    LumenTypeahead,
    LumenPullRefresh,
)


def hydrate(app) -> None:
    """Pull live magnitudes from the Press onto registered units."""
    get = getattr(getattr(app, "behavior", None), "get", None)
    if get is None:
        return
    pairing = (
        ("wishlist", "ids", tuple(PRESS.saved)),
        ("kanban", "cut", PRESS.lane("cut")),
        ("kanban", "make", PRESS.lane("make")),
        ("kanban", "keep", PRESS.lane("keep")),
        ("kpi", "bag", PRESS.bag),
        ("kpi", "held", PRESS.held),
        ("kpi", "placed", PRESS.placed),
        ("chips", "tags", tuple(PRESS.tags)),
        ("timeline", "events", PRESS.events()),
        ("presence", "peers", PRESS.peers),
        ("slider", "value", PRESS.pour),
        ("rating", "stars", PRESS.rating),
        ("lightbox", "slide", "folio"),
        ("lightbox", "open", False),
        ("carousel", "slide", "folio"),
    )
    for cid, field, value in pairing:
        try:
            inst = get(cid)
        except Exception:
            continue
        if inst is None:
            continue
        setattr(inst, field, value)
