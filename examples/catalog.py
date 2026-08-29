"""Pattern catalog — 99% use-case map.

Isolation-safe. Importing this module loads example and kit Components
(no Document, no Channel). The studio host registers every class once.
Ownable kit copies are the source of truth for promoted widgets.
"""
from __future__ import annotations

from typing import Any

from examples.foundation import Counter, Toggle, Planes
from examples.chrome import Tabs, Accordion, Dropdown, Drawer
from examples.shell import AppShell, Breadcrumbs, BottomNav, Popover, OverflowMenu
from examples.overlays import Toasts, Confirm, Palette, Banner
from examples.forms import SignupForm, Wizard, Search
from examples.fields import (
    ChoiceGroup,
    Combobox,
    DateField,
    FileDrop,
    OtpGate,
    PasswordField,
    Autosave,
    LimitedNote,
)
from examples.lists import Shelf, OptimisticList, Pages, UndoSnack
from examples.feeds import Carousel, Comments, ReorderList, ActivityFeed
from examples.navigation import ShopView, MasterDetail
from examples.table_board import DataTable
from examples.systems import (
    Chat,
    NotifyCenter,
    Tree,
    Consent,
    Theme,
    Stepper,
    InlineEdit,
)
from examples.commerce_more import Coupon, CheckoutFlow, StockBadge, CompareTray
from examples.ops import (
    Calendar,
    CopyClip,
    Settings,
    OfflineBanner,
    Shortcuts,
)
from examples.motion_xor import MotionBox, ShareSeat
from ux_compose.kit.rating import Rating
from ux_compose.kit.kanban import Kanban
from ux_compose.kit.timeline import Timeline
from ux_compose.kit.kpi import Kpi
from ux_compose.kit.slider import Slider
from ux_compose.kit.lightbox import Lightbox
from ux_compose.kit.wishlist import Wishlist
from ux_compose.kit.progress import Progress
from ux_compose.kit.empty import Empty
from ux_compose.kit.presence import Presence
from ux_compose.kit.chips import Chips
from ux_compose.kit.skeleton import Skeleton
from examples.live_caps import LiveOrder
from examples.modal import ConfirmModal as DemoModal

# Product cart (atelier) — same class at L1–L3.
from apps.atelier_shop.shop import Cart as ShopCart, ConfirmModal as ShopModal


def _p(
    slug: str,
    group: str,
    title: str,
    kicker: str,
    summary: str,
    laws: tuple[str, ...],
    detail: str,
    component: type,
    companions: tuple[type, ...] = (),
    file: str = "",
) -> dict[str, Any]:
    return {
        "slug": slug,
        "group": group,
        "title": title,
        "kicker": kicker,
        "summary": summary,
        "laws": laws,
        "detail": detail,
        "component": component,
        "companions": companions,
        "file": file,
    }


PATTERNS: list[dict[str, Any]] = [
    _p(
        "counter",
        "Foundation",
        "Counter",
        "RefState magnitude · MorphState stamp · Cap-protected reset",
        "The hello path. Increment is public. Reset is authority.",
        ("Ops-as-data", "Cap Law", "Progressive Superpower"),
        "n lives in RefState because Channel's session plane refuses quantity "
        "MorphState values. stamp is a qualitative dirty tick so the unit still "
        "morphs. Return update_with(self, plan) — never mix html= onto the Plan (XOR). "
        "The same class is valid at L1 dispatch and L3 Channel+Motion.",
        Counter,
        file="examples/foundation.py",
    ),
    _p(
        "toggle",
        "Foundation",
        "Toggle",
        "Boolean MorphState",
        "On/off chrome. Booleans are qualitative — legal on the session plane.",
        ("Ops-as-data",),
        "Flip mutates MorphState(False|True). No Caps: this is not money, delete, "
        "or identity. Motion can later rise-enter #toggle with zero rewrite.",
        Toggle,
        file="examples/foundation.py",
    ),
    _p(
        "planes",
        "Foundation",
        "Morph vs Ref",
        "What dirties a unit",
        "RefState memory is silent. Without a stamp tick the view will not change.",
        ("Ops-as-data",),
        "Three verbs: change shown (MorphState), bump silent without tick, bump "
        "silent and tick. This is the most common authoring bug — lists and "
        "counters must tick when their payload lives in RefState.",
        Planes,
        file="examples/foundation.py",
    ),
    _p(
        "tabs",
        "Chrome",
        "Tabs",
        "One MorphState key",
        "Tabs morph one region. They do not remount the page.",
        ("Morph-then-Play",),
        "tab is a name, not an index. Panels keep stable ids (#tab-cut) so a "
        "later stagger Plan can address survivors. Opening a tab is public.",
        Tabs,
        file="examples/chrome.py",
    ),
    _p(
        "accordion",
        "Chrome",
        "Accordion",
        "Set of open ids",
        "Several panels may be open. The set is a tuple of names.",
        ("Ops-as-data",),
        "toggle adds/removes a key. Nested pages are not a second Component tree "
        "inside the accordion — Host may dispatch a sibling if needed.",
        Accordion,
        file="examples/chrome.py",
    ),
    _p(
        "dropdown",
        "Chrome",
        "Dropdown",
        "Open flag + value",
        "Menu presence is MorphState. The chosen value is MorphState too.",
        ("Ops-as-data",),
        "Click-away is Host JS. State stays on the Component. Choose closes.",
        Dropdown,
        file="examples/chrome.py",
    ),
    _p(
        "drawer",
        "Chrome",
        "Drawer",
        "Sheet from the side",
        "Same shape as a modal — different CSS. Presence flag only.",
        ("Document SSoT",),
        "A drawer is not a second Document. One HTML shell, many units.",
        Drawer,
        file="examples/chrome.py",
    ),
    _p(
        "modal",
        "Chrome",
        "Modal",
        "Open MorphState · payload RefState · Cap confirm",
        "The elevated modal from examples/modal.py — used by the shop too.",
        ("Cap Law", "Document SSoT"),
        "open/close are public. confirm is Cap-protected. Hidden when closed so "
        "the morph target id remains in the tree (Motion can address it).",
        DemoModal,
        file="examples/modal.py",
    ),
    _p(
        "app-shell",
        "Chrome",
        "App shell",
        "Named route + collapsed rail",
        "Product frame. Regions morph in place. Caps stay off chrome.",
        ("Document SSoT", "Ops-as-data"),
        "current is a named route MorphState. collapsed is a boolean. Body copy "
        "is Host data. This is not a second Document and not a client router.",
        AppShell,
        file="examples/shell.py",
    ),
    _p(
        "crumbs",
        "Chrome",
        "Breadcrumbs",
        "Tuple of names",
        "Trail truncates on click. Last crumb is the page, not a link.",
        ("Ops-as-data",),
        "path is MorphState(tuple of names). Never store depth as MorphState(int). "
        "Dive/reset are public — they only rewrite the trail.",
        Breadcrumbs,
        file="examples/shell.py",
    ),
    _p(
        "bottom-nav",
        "Chrome",
        "Bottom nav",
        "Four named destinations",
        "Mobile tab bar. Same encoding as Tabs — one MorphState key.",
        ("Ops-as-data",),
        "A fifth item becomes overflow, not a fifth tab. Badge counts live on the "
        "destination unit (RefState + stamp), never on the nav chrome.",
        BottomNav,
        file="examples/shell.py",
    ),
    _p(
        "popover",
        "Chrome",
        "Popover",
        "Open flag + named pin",
        "Anchored panel. Rest of the page stays live. Not a modal.",
        ("Document SSoT",),
        "Click-away is Host JS. pin and open are qualitative MorphState. "
        "Use a modal only when the rest of the page must block.",
        Popover,
        file="examples/shell.py",
    ),
    _p(
        "overflow",
        "Chrome",
        "Overflow",
        "Kebab menu",
        "Opening is public. Destructive verbs still take Caps on their own unit.",
        ("Ops-as-data", "Cap Law"),
        "last chosen key is RefState + stamp. Overflow records intent; it does "
        "not spend authority. Archive lives on the table with records.archive.",
        OverflowMenu,
        file="examples/shell.py",
    ),
    _p(
        "toasts",
        "Overlays",
        "Toasts",
        "One-shot messages",
        "notify() is the Op. This unit shows a short stack.",
        ("Ops-as-data",),
        "Items in RefState, stamp dirties. Push is public. Domain success still "
        "goes through notify so agents and the browser share the same Op.",
        Toasts,
        file="examples/overlays.py",
    ),
    _p(
        "confirm",
        "Overlays",
        "Confirm",
        "Public ask · protected confirm",
        "Destroying a row is an authority event.",
        ("Cap Law",),
        "ask stores the target in RefState and opens. confirm requires items.delete. "
        "Offline strict_caps refuses. Live host must mint.",
        Confirm,
        file="examples/overlays.py",
    ),
    _p(
        "lightbox",
        "Overlays",
        "Lightbox",
        "Ownable kit · named slides",
        "Media viewer. The slide is a name, not an index.",
        ("Ops-as-data", "Morph-then-Play"),
        "open is MorphState. slide is a named key (same as kit Carousel). "
        "Swipe lives on Prev / Next. Overlay is presence — the card is not a containing block. "
        "Copy with uxcompose add lightbox.",
        Lightbox,
        file="src/ux_compose/kit/lightbox.py",
    ),
    _p(
        "palette",
        "Overlays",
        "Command palette",
        "Query MorphState",
        "Filter commands. Matches re-render on every type.",
        ("Ops-as-data",),
        "Offline we filter a tuple. Live would debounce on the Host with a RefState "
        "request token so stale responses are ignored.",
        Palette,
        file="examples/overlays.py",
    ),
    _p(
        "banner",
        "Overlays",
        "Banner",
        "Announcement flag",
        "A one-shot MorphState. Not a second Document.",
        ("Document SSoT",),
        "Dismiss/show. Feature banners, consent, maintenance all share this shape.",
        Banner,
        file="examples/overlays.py",
    ),
    _p(
        "signup",
        "Forms",
        "Form validation",
        "Field errors as MorphState",
        "Validate publicly. Create the account under a Cap.",
        ("Cap Law",),
        "error and email morph the unit. attempts is silent. create_account is "
        "account.create — fail-closed offline under strict_caps.",
        SignupForm,
        file="examples/forms.py",
    ),
    _p(
        "wizard",
        "Forms",
        "Wizard",
        "Named steps, not ints",
        "Multi-step flow. Step is a name so Channel session accepts it.",
        ("Cap Law", "Progressive Superpower"),
        "Payload (name, piece) in RefState until the last verb. place is orders.place.",
        Wizard,
        file="examples/forms.py",
    ),
    _p(
        "search",
        "Forms",
        "Search / typeahead",
        "Stale-token guard",
        "Query MorphState, hits RefState, req token RefState.",
        ("Ops-as-data",),
        "Bump req on every type. Ignore results whose token no longer matches. "
        "Debounce is Host-side; Behavior only holds the window.",
        Search,
        file="examples/forms.py",
    ),
    _p(
        "choices",
        "Forms",
        "Choice group",
        "Radio name + checkbox set",
        "Finish is one name. Extras are a tuple of names.",
        ("Ops-as-data",),
        "Radio value MorphState. Checkbox set RefState + stamp. Neither is a "
        "quantity. Same encoding as any multi-select.",
        ChoiceGroup,
        file="examples/fields.py",
    ),
    _p(
        "combobox",
        "Forms",
        "Combobox",
        "Query + value MorphState",
        "Type to filter, then pick one. Open is a flag.",
        ("Ops-as-data",),
        "Offline we filter a Host tuple. Live adds a RefState request token "
        "(see Search) so stale responses cannot paint.",
        Combobox,
        file="examples/fields.py",
    ),
    _p(
        "date",
        "Forms",
        "Date",
        "Named window · ISO silent",
        "Dates are not ints. Window is a name; ISO lives in RefState.",
        ("Ops-as-data",),
        "Channel would refuse MorphState(20260820). Named windows (today / "
        "tomorrow / week) survive the session plane. Host owns the real calendar.",
        DateField,
        file="examples/fields.py",
    ),
    _p(
        "files",
        "Forms",
        "File drop",
        "Filenames in RefState",
        "The Component never holds bytes. Count is derived.",
        ("Ops-as-data", "Cap Law"),
        "Add/remove names and tick. A real upload-commit would take a Cap; "
        "listing files is public. Host owns the store.",
        FileDrop,
        file="examples/fields.py",
    ),
    _p(
        "slider",
        "Forms",
        "Slider",
        "Ownable kit · magnitude silent · band named",
        "Percent is silent. Named band (empty/low/mid/full) is MorphState.",
        ("Ops-as-data",),
        "Never MorphState(40). Stepped buttons post n as an action arg — the action "
        "writes RefState, not MorphState. Copy with uxcompose add slider.",
        Slider,
        file="src/ux_compose/kit/slider.py",
    ),
    _p(
        "otp",
        "Forms",
        "OTP gate",
        "Digits silent · verify Cap",
        "Typing is public. Crossing the gate spends authority.",
        ("Cap Law",),
        "digits RefState, error MorphState. verify requires auth.verify. Studio "
        "stand-in code is 2468. Live Host would SMS it. Fail-closed offline.",
        OtpGate,
        file="examples/fields.py",
    ),
    _p(
        "password",
        "Forms",
        "Password",
        "Bool reveal · secret silent",
        "The secret is RefState. Reveal is qualitative MorphState.",
        ("Ops-as-data",),
        "Do not put the passphrase on MorphState. Host may hash; Behavior only "
        "holds the draft and the reveal flag.",
        PasswordField,
        file="examples/fields.py",
    ),
    _p(
        "autosave",
        "Forms",
        "Autosave",
        "Dirty flag · draft silent",
        "Debounce is Host. Behavior holds the window.",
        ("Ops-as-data",),
        "dirty MorphState, draft RefState, saved is a name (clean / just-now / "
        "dirty). Save is public here; a billed persist would take a Cap.",
        Autosave,
        file="examples/fields.py",
    ),
    _p(
        "limited",
        "Forms",
        "Limited note",
        "Count is derived",
        "Store the text. Remaining characters are computed in render().",
        ("Ops-as-data",),
        "Never MorphState(remaining). LIMIT is a Host constant. Over-limit is a "
        "derived error, not a second plane.",
        LimitedNote,
        file="examples/fields.py",
    ),
    _p(
        "shelf",
        "Collections",
        "Filter + sort",
        "Keyed item ids",
        "Presence continuity: id=item-{sku} survives morph so stagger can play.",
        ("Morph-then-Play", "XOR"),
        "Plan is stagger_in on surviving selectors. No html= on the Plan. Empty "
        "state is a first-class row, not a blank stage.",
        Shelf,
        file="examples/lists.py",
    ),
    _p(
        "optimistic",
        "Collections",
        "Optimistic list",
        "Paint first, confirm or roll back",
        "Pending flag MorphState. Token RefState for stale.",
        ("Ops-as-data",),
        "add_optimistic appends a marker. confirm drops it. rollback removes it. "
        "Live continuation would be a follow_up Op from the Host.",
        OptimisticList,
        file="examples/lists.py",
    ),
    _p(
        "pages",
        "Collections",
        "Pagination",
        "Opaque cursor",
        "Load-more. Cursor is a string, never a quantity MorphState.",
        ("Ops-as-data",),
        "Host fetches the next page. Behavior holds shown + has_more + loading.",
        Pages,
        file="examples/lists.py",
    ),
    _p(
        "undo",
        "Collections",
        "Undo snackbar",
        "Public reverse of a public delete",
        "Remove now, restore during the window.",
        ("Ops-as-data",),
        "If delete were Cap-protected, undo would be too (lineage / reverse). "
        "Here both verbs are public so the snack is honest offline.",
        UndoSnack,
        file="examples/lists.py",
    ),
    _p(
        "table",
        "Collections",
        "Data table",
        "Sort · select · bulk Cap",
        "Sort key qualitative. Selection in RefState. Archive is authority.",
        ("Cap Law",),
        "bulk_archive requires records.archive. Live host mints or refuses.",
        DataTable,
        file="examples/table_board.py",
    ),
    _p(
        "kanban",
        "Collections",
        "Kanban",
        "Ownable kit · three lanes · archive Cap",
        "Moving a card is public. Archiving spends items.archive.",
        ("Ops-as-data", "Cap Law"),
        "Each column is a RefState tuple of ids. move rewrites membership and ticks. "
        "Copy with uxcompose add kanban.",
        Kanban,
        file="src/ux_compose/kit/kanban.py",
    ),
    _p(
        "carousel",
        "Collections",
        "Carousel",
        "Index silent · keyed slides",
        "Media strip. Index is a magnitude. Captions are Host data.",
        ("Morph-then-Play",),
        "id=slide-{sku} survives morph. next/prev tick the stamp. Dots are named "
        "jumps posting n as an action arg — not MorphState(int).",
        Carousel,
        file="examples/feeds.py",
    ),
    _p(
        "comments",
        "Collections",
        "Comments",
        "Thread · reply-to named",
        "History in RefState. Posting is public. Moderate is a Cap.",
        ("Cap Law", "Ops-as-data"),
        "reply_to is a named MorphState. moderate requires comments.moderate. A "
        "billed or identity-gated post would take a Cap on post instead.",
        Comments,
        file="examples/feeds.py",
    ),
    _p(
        "timeline",
        "Collections",
        "Timeline",
        "Ownable kit · named filter · events silent",
        "Ordered history. Filter is a lane name, not an index.",
        ("Ops-as-data",),
        "Same encoding as a filtered shelf. Empty lane is a first-class row. "
        "Copy with uxcompose add timeline.",
        Timeline,
        file="src/ux_compose/kit/timeline.py",
    ),
    _p(
        "empty-retry",
        "Collections",
        "Empty / error / retry",
        "Ownable kit · named phase",
        "empty | loading | error | ready are part of the design.",
        ("Ops-as-data",),
        "phase MorphState. Body RefState. Retry is public; a billed refetch would "
        "take a Cap. Copy with uxcompose add empty.",
        Empty,
        file="src/ux_compose/kit/empty.py",
    ),
    _p(
        "reorder",
        "Collections",
        "Reorder",
        "Stable item ids · order silent",
        "Moving a row is public. Archiving it would take a Cap.",
        ("Morph-then-Play",),
        "order is a RefState tuple. id=ord-{sku} is presence. Up/down rewrite "
        "membership and tick. Same shape as kanban.move for a single list.",
        ReorderList,
        file="examples/feeds.py",
    ),
    _p(
        "activity",
        "Collections",
        "Activity",
        "Opaque cursor · items silent",
        "Infinite-ish feed. Cursor is a string, never MorphState(int).",
        ("Ops-as-data",),
        "Same encoding as pagination. Host owns the rest of the log. has_more is "
        "a boolean MorphState.",
        ActivityFeed,
        file="examples/feeds.py",
    ),
    _p(
        "shop-view",
        "Navigation",
        "Region swap",
        "List ↔ detail on one id",
        "The page does not remount. mode MorphState, selected RefState.",
        ("XOR", "Morph-then-Play"),
        "Plan exit/enter recipes on #shopview. html= is forbidden on enter "
        "because update_with already morphs that target.",
        ShopView,
        file="examples/navigation.py",
    ),
    _p(
        "split",
        "Navigation",
        "Master / detail",
        "Split pane",
        "Selection MorphState. Body from a Host catalog.",
        ("Ops-as-data",),
        "Two regions, one Component. A second Component is only needed when "
        "the detail has its own verbs (edit, delete).",
        MasterDetail,
        file="examples/navigation.py",
    ),
    _p(
        "cart",
        "Commerce",
        "Cart",
        "MorphState + Cap checkout + optional Plan",
        "The elevated cart. Last sku is silent. Checkout is orders.place.",
        ("Cap Law", "Morph-then-Play", "Progressive Superpower"),
        "The product bag: lines in RefState, stamp as MorphState so Channel "
        "session accepts it. checkout is orders.place — the host mints.",
        ShopCart,
        file="examples/cart.py",
    ),
    _p(
        "stepper",
        "Commerce",
        "Quantity stepper",
        "Magnitude in RefState",
        "PDP quantity. Never MorphState(int) on the Channel session plane.",
        ("Cap Law",),
        "The same encoding as the product bag: stamp dirties, qty is silent.",
        Stepper,
        file="examples/systems.py",
    ),
    _p(
        "rating",
        "Commerce",
        "Star rating",
        "Ownable kit · named, not numeric",
        "one|two|three|four|five — qualitative MorphState.",
        ("Ops-as-data",),
        "Ints on MorphState fail live. Names survive. Copy with uxcompose add rating.",
        Rating,
        file="src/ux_compose/kit/rating.py",
    ),
    _p(
        "wishlist",
        "Commerce",
        "Wishlist",
        "Ownable kit · ids silent · heart public",
        "Saving is not placing. Heart/unheart is public.",
        ("Ops-as-data",),
        "ids RefState + stamp. Checkout remains a Cap on the cart unit. "
        "Copy with uxcompose add wishlist.",
        Wishlist,
        file="src/ux_compose/kit/wishlist.py",
    ),
    _p(
        "coupon",
        "Commerce",
        "Coupon",
        "Code is a name · redeem Cap",
        "Checking is public. Redeeming changes the payable — authority.",
        ("Cap Law",),
        "code MorphState (string). off RefState. redeem requires coupons.redeem. "
        "Studio stand-ins: HOUSE10, LINEN. Fail-closed without a mint.",
        Coupon,
        file="examples/commerce_more.py",
    ),
    _p(
        "checkout",
        "Commerce",
        "Checkout",
        "Named steps · place Cap",
        "who / ship / pay / review. Payload silent until Place.",
        ("Cap Law", "Progressive Superpower"),
        "Same shape as the wizard, specialized for a storefront. place is "
        "orders.place. Studio mints on the Place button so you can see success.",
        CheckoutFlow,
        file="examples/commerce_more.py",
    ),
    _p(
        "stock",
        "Commerce",
        "Stock",
        "Qty silent · band named",
        "ok / low / out is what the session plane is allowed to see.",
        ("Ops-as-data",),
        "Never MorphState(3). qty RefState; band derived into MorphState. Sell is "
        "public here; a real sale would be orders.place on the cart.",
        StockBadge,
        file="examples/commerce_more.py",
    ),
    _p(
        "compare",
        "Commerce",
        "Compare",
        "Max three ids",
        "Selection is a list — RefState + stamp.",
        ("Ops-as-data",),
        "LIMIT is a Host constant. Toggle refuses a fourth. Same encoding as "
        "wishlist with a ceiling.",
        CompareTray,
        file="examples/commerce_more.py",
    ),
    _p(
        "live-order",
        "Live Caps",
        "Cap checkout",
        "Authority Clock",
        "Place without a Cap is refused. Host-mint succeeds.",
        ("Cap Law", "Isolation Law"),
        "Product never imports ux_channel. Studio /act uses App.submit_intent_async. "
        "After use_channel, dispatch is Host-internal — live verification is Intent.",
        LiveOrder,
        file="examples/live_caps.py",
    ),
    _p(
        "motion-box",
        "Motion",
        "Morph-then-Play",
        "XOR-safe hop",
        "Plan has no html=. Patch is live render().",
        ("XOR", "Morph-then-Play"),
        "update_with(self, scene(...).enter(#id, rise.enter())). Without ux-motion "
        "the morph still lands. Zero rewrite at L3.",
        MotionBox,
        file="examples/motion_xor.py",
    ),
    _p(
        "share",
        "Motion",
        "Shared element",
        "scene.share continuity",
        "Leave and arrive selectors must exist after morph.",
        ("XOR", "Morph-then-Play"),
        "share id is identity, not a CSS class. Morph the unit first, then play.",
        ShareSeat,
        file="examples/motion_xor.py",
    ),
    _p(
        "chat",
        "Systems",
        "Chat",
        "Typing indicator + lines",
        "Presence flag MorphState. History RefState.",
        ("Ops-as-data",),
        "Send is public here. A billed or moderated send would take a Cap.",
        Chat,
        file="examples/systems.py",
    ),
    _p(
        "inbox",
        "Systems",
        "Notification center",
        "Badge from RefState",
        "Unread count is magnitude — stamp + RefState.",
        ("Ops-as-data",),
        "Open is MorphState. Mark-read ticks the badge to zero.",
        NotifyCenter,
        file="examples/systems.py",
    ),
    _p(
        "tree",
        "Systems",
        "Tree",
        "Expanded ids",
        "File browser / nested nav. Expand set + selected key.",
        ("Ops-as-data",),
        "Children render only when the parent id is in expanded. Host owns the node list.",
        Tree,
        file="examples/systems.py",
    ),
    _p(
        "skeleton",
        "Systems",
        "Skeleton / loading",
        "Ownable kit · loading MorphState",
        "Empty, loading, ready are part of the design.",
        ("Ops-as-data", "Morph-then-Play"),
        "loading=True paints the gate. arrive swaps body in. Reload returns to the gate. "
        "Copy with uxcompose add skeleton.",
        Skeleton,
        file="src/ux_compose/kit/skeleton.py",
    ),
    _p(
        "consent",
        "Systems",
        "Consent gate",
        "Cookie / motion permission",
        "Motion recipes stay off until allow.",
        ("Cap Law",),
        "Choice is MorphState(ask|allow|essential). Host reads it before attaching players.",
        Consent,
        file="examples/systems.py",
    ),
    _p(
        "theme",
        "Systems",
        "Locale",
        "Locale MorphState",
        "Paper house stays light-only. Copy switches.",
        ("Ops-as-data",),
        "Theme/locale/currency switchers are this shape. Never a second Document.",
        Theme,
        file="examples/systems.py",
    ),
    _p(
        "chips",
        "Systems",
        "Chips / tags",
        "Ownable kit · tag set as RefState",
        "Add/remove names. Stamp dirties the unit.",
        ("Ops-as-data",),
        "Same encoding as a multi-select. Domain tags stay Host-owned. "
        "Copy with uxcompose add chips.",
        Chips,
        file="src/ux_compose/kit/chips.py",
    ),
    _p(
        "inline",
        "Systems",
        "Inline edit",
        "Pencil / save",
        "editing MorphState. text RefState.",
        ("Ops-as-data",),
        "contenteditable is Host chrome. Behavior holds the value and the mode.",
        InlineEdit,
        file="examples/systems.py",
    ),
    _p(
        "calendar",
        "Systems",
        "Calendar",
        "Named month · day silent · book Cap",
        "A grid of days is Host chrome. Booking spends authority.",
        ("Cap Law",),
        "month MorphState (july/august/september). day RefState. booked tuple "
        "silent. book requires bookings.create. Never MorphState(14).",
        Calendar,
        file="examples/ops.py",
    ),
    _p(
        "progress",
        "Systems",
        "Progress",
        "Ownable kit · pct silent · phase named",
        "idle / run / done. Percent is a magnitude.",
        ("Ops-as-data",),
        "Bar width is a derived band class (empty/low/mid/full), not an inline "
        "quantity on MorphState. bump writes RefState and ticks. "
        "Copy with uxcompose add progress.",
        Progress,
        file="src/ux_compose/kit/progress.py",
    ),
    _p(
        "copy",
        "Systems",
        "Copy",
        "Bool copied · text silent",
        "Clipboard stand-in. Host JS would talk to navigator.clipboard.",
        ("Ops-as-data",),
        "copied MorphState. text RefState. The Component never needs the "
        "clipboard API — Host enhancement can no-op when it is missing.",
        CopyClip,
        file="examples/ops.py",
    ),
    _p(
        "settings",
        "Systems",
        "Settings",
        "Named prefs · wipe Cap",
        "Density and motion are names. Wipe is admin.reset lineage.",
        ("Cap Law", "Ops-as-data"),
        "Paper house stays light-only. Prefs are qualitative MorphState. wipe "
        "fail-closed offline; live host must mint.",
        Settings,
        file="examples/ops.py",
    ),
    _p(
        "offline",
        "Systems",
        "Offline banner",
        "Bool connectivity",
        "Copy switches. Actions queue. Not a second Document.",
        ("Document SSoT",),
        "online MorphState. Host would drive this from navigator.onLine. "
        "Queued verbs stay on the Component until the wire returns.",
        OfflineBanner,
        file="examples/ops.py",
    ),
    _p(
        "presence",
        "Systems",
        "Presence",
        "Ownable kit · self named · peers silent",
        "here / away / focus. Peer list is RefState.",
        ("Ops-as-data",),
        "Self status is qualitative. Counts of peers are derived, never "
        "MorphState(int). Copy with uxcompose add presence.",
        Presence,
        file="src/ux_compose/kit/presence.py",
    ),
    _p(
        "kpi",
        "Systems",
        "KPI strip",
        "Ownable kit · magnitudes silent · stamp dirties",
        "Dashboard numbers from Host DB, never from the session plane.",
        ("Ops-as-data", "Cap Law"),
        "bag / held / placed are RefState. tick_up simulates a sale. "
        "reset spends admin.reset. Copy with uxcompose add kpi.",
        Kpi,
        file="src/ux_compose/kit/kpi.py",
    ),
    _p(
        "shortcuts",
        "Systems",
        "Shortcuts",
        "Query MorphState",
        "Keyboard overlay. Same encoding as the command palette.",
        ("Ops-as-data",),
        "open flag + query. Host JS would bind '?'. Filter is public. No Caps: "
        "this is chrome, not money.",
        Shortcuts,
        file="examples/ops.py",
    ),
]


GROUPS = (
    "Foundation",
    "Chrome",
    "Overlays",
    "Forms",
    "Collections",
    "Navigation",
    "Commerce",
    "Live Caps",
    "Motion",
    "Systems",
)


def by_slug(slug: str) -> dict[str, Any] | None:
    for row in PATTERNS:
        if row["slug"] == slug:
            return row
    return None


def all_components() -> list[type]:
    seen: dict[str, type] = {}
    for row in PATTERNS:
        for cls in (row["component"], *row["companions"]):
            key = getattr(cls, "id", cls.__name__)
            seen[key] = cls
    # Product shop units (also registered so /shop works on the same App).
    seen[ShopCart.id] = ShopCart
    seen[ShopModal.id] = ShopModal
    return list(seen.values())
