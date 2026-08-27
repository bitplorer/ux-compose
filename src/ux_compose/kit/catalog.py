"""Registry of ownable kit Components (CLI + docs).

shadcn-style: ``uxcompose add login`` copies the module into the app.
The app owns the file. The library keeps the source of truth.
"""

from __future__ import annotations

from typing import TypedDict


class KitEntry(TypedDict):
    name: str
    module: str
    stem: str
    exports: list[str]
    description: str
    css: bool
    page: bool


CATALOG: dict[str, KitEntry] = {
    "login": {
        "name": "Login",
        "module": "ux_compose.kit.login",
        "stem": "login",
        "exports": ["Login", "AuthDecision"],
        "description": "Sign-in / sign-up card. Reveal attaches. Submit is a Cap.",
        "css": False,
        "page": True,
    },
    "tabs": {
        "name": "Tabs",
        "module": "ux_compose.kit.tabs",
        "stem": "tabs",
        "exports": ["Tabs"],
        "description": "Segmented tabs. One MorphState key. Public select.",
        "css": False,
        "page": True,
    },
    "accordion": {
        "name": "Accordion",
        "module": "ux_compose.kit.accordion",
        "stem": "accordion",
        "exports": ["Accordion"],
        "description": "Open ids as a MorphState tuple. Several panels may be open.",
        "css": False,
        "page": True,
    },
    "dropdown": {
        "name": "Dropdown",
        "module": "ux_compose.kit.dropdown",
        "stem": "dropdown",
        "exports": ["Dropdown"],
        "description": "Menu is presence. Value is a named key.",
        "css": False,
        "page": True,
    },
    "dialog": {
        "name": "Dialog",
        "module": "ux_compose.kit.dialog",
        "stem": "dialog",
        "exports": ["Dialog"],
        "description": "Public ask, Cap-protected confirm. Override on_confirm().",
        "css": False,
        "page": True,
    },
    "sheet": {
        "name": "Sheet",
        "module": "ux_compose.kit.sheet",
        "stem": "sheet",
        "exports": ["Sheet"],
        "description": "Edge panel. Close / Done accept swipe.right. No root swipe.",
        "css": False,
        "page": True,
    },
    "toast": {
        "name": "Toast",
        "module": "ux_compose.kit.toast",
        "stem": "toast",
        "exports": ["Toast"],
        "description": "Server list is authority. Push is public.",
        "css": False,
        "page": True,
    },
    "command": {
        "name": "Command",
        "module": "ux_compose.kit.command",
        "stem": "command",
        "exports": ["Command"],
        "description": "Command palette. Query attaches. Override on_run().",
        "css": False,
        "page": True,
    },
    "table": {
        "name": "Table",
        "module": "ux_compose.kit.table",
        "stem": "table",
        "exports": ["Table"],
        "description": "Sort key MorphState, selection RefState. Archive is a Cap.",
        "css": False,
        "page": True,
    },
    "pagination": {
        "name": "Pagination",
        "module": "ux_compose.kit.pagination",
        "stem": "pagination",
        "exports": ["Pagination"],
        "description": "Opaque page keys. Windowed numbers, not one button per page.",
        "css": False,
        "page": True,
    },
    "combobox": {
        "name": "Combobox",
        "module": "ux_compose.kit.combobox",
        "stem": "combobox",
        "exports": ["Combobox"],
        "description": "Type to filter, then pick. Query attaches on morph.",
        "css": False,
        "page": True,
    },
    "sidebar": {
        "name": "Sidebar",
        "module": "ux_compose.kit.sidebar",
        "stem": "sidebar",
        "exports": ["Sidebar"],
        "description": "Collapsible rail. Active key is MorphState.",
        "css": False,
        "page": True,
    },
    "breadcrumb": {
        "name": "Breadcrumb",
        "module": "ux_compose.kit.breadcrumb",
        "stem": "breadcrumb",
        "exports": ["Breadcrumb"],
        "description": "Trail of named crumbs. Walking back is public.",
        "css": False,
        "page": True,
    },
    "stepper": {
        "name": "Stepper",
        "module": "ux_compose.kit.stepper",
        "stem": "stepper",
        "exports": ["Stepper"],
        "description": "Named steps. Finish spends flow.finish.",
        "css": False,
        "page": True,
    },
    "carousel": {
        "name": "Carousel",
        "module": "ux_compose.kit.carousel",
        "stem": "carousel",
        "exports": ["Carousel"],
        "description": "Named slides. Overlay prev/next. Sliding pip coalesces on morph.",
        "css": False,
        "page": True,
    },
    "calendar": {
        "name": "Calendar",
        "module": "ux_compose.kit.calendar",
        "stem": "calendar",
        "exports": ["Calendar"],
        "description": "Month and day are named keys. Override on_pick().",
        "css": False,
        "page": True,
    },
    "select": {
        "name": "Select",
        "module": "ux_compose.kit.select",
        "stem": "select",
        "exports": ["Select"],
        "description": "Grouped options. Value is a name. Click-away scrim.",
        "css": False,
        "page": True,
    },
    "otp": {
        "name": "Otp",
        "module": "ux_compose.kit.otp",
        "stem": "otp",
        "exports": ["Otp"],
        "description": "Six digits attach. Verify spends auth.otp.",
        "css": False,
        "page": True,
    },
    "plans": {
        "name": "Plans",
        "module": "ux_compose.kit.plans",
        "stem": "plans",
        "exports": ["Plans"],
        "description": "Radio cards. One named plan. Override on_choose().",
        "css": False,
        "page": True,
    },
    "actionsheet": {
        "name": "ActionSheet",
        "module": "ux_compose.kit.actionsheet",
        "stem": "actionsheet",
        "exports": ["ActionSheet"],
        "description": "Bottom sheet. Handle swipe-down dismisses. Rows stay click.",
        "css": False,
        "page": True,
    },
    "contextmenu": {
        "name": "ContextMenu",
        "module": "ux_compose.kit.contextmenu",
        "stem": "contextmenu",
        "exports": ["ContextMenu"],
        "description": "Click or longpress. Floating panel, not a native list.",
        "css": False,
        "page": True,
    },
    "typeahead": {
        "name": "Typeahead",
        "module": "ux_compose.kit.typeahead",
        "stem": "typeahead",
        "exports": ["Typeahead"],
        "description": "Live filter on input delay:. The field is the control.",
        "css": False,
        "page": True,
    },
    "pullrefresh": {
        "name": "PullRefresh",
        "module": "ux_compose.kit.pullrefresh",
        "stem": "pullrefresh",
        "exports": ["PullRefresh"],
        "description": "Vertical swipe synthesizer. Refresh control accepts swipe.down.",
        "css": False,
        "page": True,
    },
}


def list_components() -> list[KitEntry]:
    return list(CATALOG.values())


def resolve(name: str) -> KitEntry:
    key = name.strip().lower().replace("-", "_")
    if key in CATALOG:
        return CATALOG[key]
    for k, meta in CATALOG.items():
        if meta["name"].lower() == key:
            return meta
    raise KeyError(key)
