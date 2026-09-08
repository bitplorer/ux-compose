"""Ownable kit. Prefer the CLI copy — do not import this in product code.

    uxcompose add --list
    uxcompose add tabs
    uxcompose add dialog --page

The library keeps the source of truth. The copy is yours to edit.
``from ux_compose.kit import Login`` stays for tests, the Atelier, and
agents — product apps own the file after ``add``.

See docs/ARCHITECTURE.md (one catalog rule).
"""

from ux_compose.kit.accordion import Accordion
from ux_compose.kit.alert import Alert
from ux_compose.kit.alertdialog import AlertDialog
from ux_compose.kit.avatar import Avatar
from ux_compose.kit.badge import Badge
from ux_compose.kit.banner import Banner
from ux_compose.kit.bottomnav import BottomNav
from ux_compose.kit.breadcrumb import Breadcrumb
from ux_compose.kit.calendar import Calendar
from ux_compose.kit.card import Card
from ux_compose.kit.carousel import Carousel
from ux_compose.kit.chat import Chat
from ux_compose.kit.combobox import Combobox
from ux_compose.kit.command import Command
from ux_compose.kit.cta import Cta
from ux_compose.kit.descriptionlist import DescriptionList
from ux_compose.kit.dialog import Dialog
from ux_compose.kit.drawer import Drawer
from ux_compose.kit.dropdown import Dropdown
from ux_compose.kit.emptystate import EmptyState
from ux_compose.kit.featuregrid import FeatureGrid
from ux_compose.kit.fieldset import Fieldset
from ux_compose.kit.fileupload import FileUpload
from ux_compose.kit.filterbar import FilterBar
from ux_compose.kit.footer import Footer
from ux_compose.kit.formlayout import FormLayout
from ux_compose.kit.hero import Hero
from ux_compose.kit.hovercard import HoverCard
from ux_compose.kit.login import AuthDecision, Login
from ux_compose.kit.logocloud import LogoCloud
from ux_compose.kit.menubar import Menubar
from ux_compose.kit.multiselect import MultiSelect
from ux_compose.kit.navbar import Navbar
from ux_compose.kit.navmenu import NavMenu
from ux_compose.kit.newsletter import Newsletter
from ux_compose.kit.otp import Otp
from ux_compose.kit.pagination import Pagination
from ux_compose.kit.plans import Plans
from ux_compose.kit.popover import Popover
from ux_compose.kit.pricingsection import PricingSection
from ux_compose.kit.progress import Progress
from ux_compose.kit.questionnaire import Questionnaire
from ux_compose.kit.searchbar import SearchBar
from ux_compose.kit.select import Select
from ux_compose.kit.separator import Separator
from ux_compose.kit.sheet import Sheet
from ux_compose.kit.sidebar import Sidebar
from ux_compose.kit.skeleton import Skeleton
from ux_compose.kit.slider import Slider
from ux_compose.kit.spinbutton import SpinButton
from ux_compose.kit.stats import Stats
from ux_compose.kit.stepper import Stepper
from ux_compose.kit.switch import Switch
from ux_compose.kit.table import Table
from ux_compose.kit.tabs import Tabs
from ux_compose.kit.tagsinput import TagsInput
from ux_compose.kit.testimonials import Testimonials
from ux_compose.kit.themeswitch import ThemeSwitch
from ux_compose.kit.toast import Toast
from ux_compose.kit.togglegroup import ToggleGroup
from ux_compose.kit.toolbar import Toolbar
from ux_compose.kit.tooltip import Tooltip
from ux_compose.kit.usermenu import UserMenu
from ux_compose.kit.datepicker import DatePicker
from ux_compose.kit.actionsheet import ActionSheet
from ux_compose.kit.contextmenu import ContextMenu
from ux_compose.kit.typeahead import Typeahead
from ux_compose.kit.pullrefresh import PullRefresh
from ux_compose.kit.overlay import OverlayChrome, overlay
from ux_compose.kit.rating import Rating
from ux_compose.kit.timeline import Timeline

__all__ = [
    "AuthDecision",
    "Login",
    "Tabs",
    "Accordion",
    "Dropdown",
    "Dialog",
    "Sheet",
    "Drawer",
    "Toast",
    "Command",
    "Table",
    "Pagination",
    "Combobox",
    "Sidebar",
    "Breadcrumb",
    "Stepper",
    "Carousel",
    "Calendar",
    "Select",
    "Otp",
    "Plans",
    "ActionSheet",
    "ContextMenu",
    "Typeahead",
    "PullRefresh",
    "Navbar",
    "NavMenu",
    "UserMenu",
    "Popover",
    "Tooltip",
    "AlertDialog",
    "FormLayout",
    "Fieldset",
    "DatePicker",
    "Switch",
    "Card",
    "EmptyState",
    "Stats",
    "Alert",
    "Banner",
    "Progress",
    "Skeleton",
    "Hero",
    "Footer",
    "Cta",
    "Avatar",
    "Badge",
    "HoverCard",
    "SearchBar",
    "FileUpload",
    "TagsInput",
    "MultiSelect",
    "DescriptionList",
    "FeatureGrid",
    "Testimonials",
    "Newsletter",
    "BottomNav",
    "Separator",
    "Slider",
    "Menubar",
    "Toolbar",
    "ToggleGroup",
    "SpinButton",
    "ThemeSwitch",
    "FilterBar",
    "Chat",
    "Questionnaire",
    "PricingSection",
    "LogoCloud",
    "Timeline",
    "Rating",
    "OverlayChrome",
    "overlay",
]
