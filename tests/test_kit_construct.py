"""Cut 1: render slots + shell=False usable units. No Kit base.

Isolation: this file never imports ux_channel. No Cap kernel / cek-runtime / law.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ux_compose import App, HAS_DOM
from ux_compose.component import Component
from ux_compose.helpers import _serialize_tree
from ux_compose.kit.catalog import CATALOG
from ux_compose.kit.copy import copy_component
from ux_compose.kit.dialog import Dialog
from ux_compose.kit.fab import Fab
from ux_compose.kit.hovercard import HoverCard
from ux_compose.kit.popover import Popover
from ux_compose.kit.toast import Toast
from ux_compose.kit_construct import apply_slots, kit_shell

# Atelier framing that must vanish at shell=False. Empty = no demo card copy
# on the default render (runtime-only / brand-is-unit kits).
DEMO_FRAMING: dict[str, tuple[str, ...]] = {
    "accordion": ("Guide",),
    "actionsheet": ("Action sheet", "Sheet · swipe down"),
    "alert": ("No alerts",),
    "alertdialog": ("Alert dialog", "Interrupt"),
    "attachment": ("On the board",),
    "avatar": ("Portrait",),
    "badge": ("Stage",),
    "banner": ("Banner hidden", "Notice"),
    "bottomnav": ("The bar is a landmark",),
    "breadcrumb": ("Walking back is public",),
    "calendar": ("Date",),
    "card": ("Piece",),
    "carousel": (),
    "chart": ("Winter cuts",),
    "chat": ("Desk",),
    "colorpicker": ("A named swatch",),
    "combobox": ("Search the catalog",),
    "command": ("Type to filter. Run is public chrome.",),
    "contextmenu": ("Hold or click",),
    "countdown": ("Until",),
    "cta": ("Invite",),
    "datepicker": ("Pick a day",),
    "descriptionlist": ("Facts",),
    "dialog": ("Confirm a delete", "Authority"),
    "diff": ("Revise",),
    "drawer": ("Edge",),
    "dropdown": ("Material",),
    "emptystate": ("Empty",),
    "fab": ("A new thing",),
    "featuregrid": ("How it is made",),
    "feed": ("Activity",),
    "fieldset": ("Finish",),
    "fileupload": ("Attach a note",),
    "filterbar": ("The winter list",),
    "footer": (),
    "formlayout": ("Write it down",),
    "hero": ("Studio",),
    "hovercard": ("Who made this", "Preview"),
    "login": (),
    "logocloud": ("Who we keep",),
    "menubar": ("The bar",),
    "mockup": ("On the table",),
    "multiselect": ("Several names. Select-all is not a row click.",),
    "navbar": (),
    "navmenu": ("Go somewhere",),
    "newsletter": ("Winter list", "No spam, ever."),
    "otp": ("Enter the code",),
    "pagination": ("The shelf",),
    "plans": ("Choose a desk",),
    "popover": ("A quiet note",),
    "pricingsection": ("Desks",),
    "progress": ("Work",),
    "pullrefresh": ("Pull to refresh",),
    "questionnaire": ("A few questions",),
    "rating": ("Keep",),
    "resizable": ("Two desks",),
    "scrollarea": ("The long note",),
    "searchbar": ("Find",),
    "select": ("Grouped options. The value is a name.",),
    "separator": ("A pause", "Above the fold"),
    "sheet": ("Edge",),
    "sidebar": (),
    "skeleton": ("Loading the desk",),
    "slider": (),
    "spinbutton": ("Count",),
    "stats": ("Counts live on RefState",),
    "stepper": ("Flow",),
    "switch": (),
    "table": ("Pieces on the table",),
    "tabs": ("Workspace",),
    "tagsinput": ("Name the piece",),
    "testimonials": ("What they keep",),
    "themeswitch": ("Look",),
    "timeline": ("What happened",),
    "toast": ("Notices", "notify() is the Op"),
    "togglegroup": ("Range",),
    "toolbar": ("The strip",),
    "tooltip": ("What this does",),
    "tree": ("Rooms",),
    "typeahead": ("Typeahead",),
    "usermenu": ("Session",),
}


def _html(inst) -> str:
    if HAS_DOM:
        return inst.__render__(pretty=False)
    return _serialize_tree(inst.render())


def test_kit_base_class_gone():
    import ux_compose.kit_construct as kc

    assert not hasattr(kc, "Kit")
    assert not hasattr(kc, "apply_kit_construct")
    assert callable(apply_slots)
    assert callable(kit_shell)
    assert issubclass(Fab, Component)
    assert not any(c.__name__ == "Kit" for c in Fab.__mro__)


def test_fab_render_slots_shell_false_omits_demo_title():
    inst = Fab()
    tree = inst.render(actions=(("a", "A"),), shell=False)
    html = _serialize_tree(tree)
    assert "A new thing" not in html
    assert "Make" not in html
    assert "The round button is the verb" not in html
    assert "A" in html
    assert 'role="menuitem"' in html
    assert 'id="fab"' in html
    assert inst.ACTIONS == (("a", "A"),)
    assert inst.shell is False


def test_fab_zero_arg_keeps_atelier_demo():
    inst = Fab()
    html = _html(inst)
    assert "A new thing" in html
    assert "New note" in html
    assert "New cut" in html
    assert inst.ACTIONS == Fab.ACTIONS


def test_fab_unknown_slot_fails_closed():
    with pytest.raises(TypeError, match="unexpected slots"):
        Fab().render(nope=1)


def test_fab_subclass_const_then_instance_wins():
    class Mine(Fab):
        id = "fab"
        ACTIONS = (("x", "X"),)

    plain = Mine()
    assert plain.ACTIONS == (("x", "X"),)
    html = _html(plain)
    assert "X" in html

    inst = Mine()
    inst.render(actions=(("z", "Z"),), shell=False)
    assert inst.ACTIONS == (("z", "Z"),)
    html = _html(inst)
    assert "Z" in html
    assert "X" not in html
    assert "A new thing" not in html


def test_fab_behavior_add_zero_arg_still_greens():
    app = App.boot("FabConstruct", strict_caps=False)
    app.add(Fab)
    inst = app.behavior.get("fab")
    html = _html(inst)
    assert "A new thing" in html
    assert "New note" in html
    app.dispatch("fab.toggle")
    html = _html(app.behavior.get("fab"))
    assert "New note" in html


def test_fab_render_slots_survive_morph():
    app = App.boot("FabSlotsMorph", strict_caps=False)
    app.add(Fab)
    inst = app.behavior.get("fab")
    inst.render(actions=(("a", "A"),), shell=False)
    assert inst.ACTIONS == (("a", "A"),)
    app.dispatch("fab.toggle")
    later = app.behavior.get("fab")
    html = _html(later)
    assert "A" in html
    assert "A new thing" not in html
    assert later.ACTIONS == (("a", "A"),)
    assert later.shell is False


def test_apply_slots_unknown_fails_closed():
    class Probe(Component):
        id = "probe"
        _SEAMS = {"actions": "ACTIONS"}
        ACTIONS = (("a", "A"),)

        def render(self, *, shell=None, **slots):
            apply_slots(self, seams=self._SEAMS, shell=shell, **slots)
            return ""

    apply_slots(Probe(), seams={"actions": "ACTIONS"})
    with pytest.raises(TypeError, match="unexpected slots"):
        Probe().render(ghost=True)


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_catalog_zero_arg_still_renders():
    for stem, meta in CATALOG.items():
        if stem in {"overlay"}:
            continue
        mod = __import__(meta["module"], fromlist=[meta["name"]])
        cls = getattr(mod, meta["name"])
        inst = cls()
        tree = inst.render()
        assert tree is not None, stem
        html = _serialize_tree(tree)
        assert f'id="{cls.id}"' in html, stem


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_add_fab_unchanged(tmp_path: Path):
    (tmp_path / "app.py").write_text("# app\n", encoding="utf-8")
    (tmp_path / "routes").mkdir()
    written = copy_component("fab", root=tmp_path)
    text = written["py"].read_text(encoding="utf-8")
    ast.parse(text)
    assert written["css"] is None
    assert written["base"] is None
    assert "from ux_compose.kit import" not in text
    assert "ux_channel" not in text
    assert not (tmp_path / "components" / "base.py").exists()


def test_demo_framing_covers_catalog():
    missing = set(CATALOG) - set(DEMO_FRAMING) - {"overlay"}
    assert not missing, f"DEMO_FRAMING missing stems: {sorted(missing)}"


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
@pytest.mark.parametrize("stem", sorted(stem for stem in CATALOG if stem != "overlay"))
def test_shell_false_omits_demo_framing(stem: str):
    meta = CATALOG[stem]
    mod = __import__(meta["module"], fromlist=[meta["name"]])
    cls = getattr(mod, meta["name"])
    inst = cls()
    inst.render(shell=False)
    html = _html(inst)
    assert f'id="{cls.id}"' in html, stem
    for phrase in DEMO_FRAMING.get(stem, ()):
        assert phrase not in html, f"{stem}: {phrase!r} leaked at shell=False"


@pytest.mark.skipif(not HAS_DOM, reason="ux-dom")
def test_alert_closed_shell_false_omits_no_alerts():
    from ux_compose.kit.alert import Alert

    inst = Alert()
    inst.render(shell=False)
    inst.open = False
    html = _html(inst)
    assert "No alerts" not in html
    assert "Show alert" in html


def test_dialog_title_refstate_slot():
    inst = Dialog()
    inst.render(title="Scrap this oak?", body="Gone for good.", shell=False)
    assert str(inst.title) == "Scrap this oak?"
    assert str(inst.body) == "Gone for good."
    html = _html(inst)
    assert "Confirm a delete" not in html


def test_toast_items_refstate_slot():
    rows = ({"id": "1", "message": "Board waxed"},)
    inst = Toast()
    inst.render(items=rows, shell=False)
    assert tuple(inst.items or ()) == rows
    html = _html(inst)
    assert "Board waxed" in html
    assert "Notices" not in html


def test_hovercard_popover_render_copy():
    card = HoverCard()
    card.render(title="Oak", body="Waxed board.", trigger="Open oak", kind="Maker", shell=False)
    assert card.TITLE == "Oak"
    assert card.TRIGGER == "Open oak"
    pop = Popover()
    pop.render(title="Restock", body="Thursday.", trigger="News", shell=False)
    assert pop.TITLE == "Restock"
    assert pop.TRIGGER == "News"
    with pytest.raises(TypeError, match="unexpected slots"):
        Popover().render(ghost=True)


def test_kit_construct_never_imports_ux_channel():
    path = ROOT / "src" / "ux_compose" / "kit_construct.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden = ("ux_channel", "cek_runtime", "cek_host")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert not any(alias.name.startswith(f) for f in forbidden)
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert not any(node.module.startswith(f) for f in forbidden)


def test_kit_modules_never_import_ux_channel():
    forbidden = ("ux_channel", "cek_runtime", "cek_host")
    kit_dir = ROOT / "src" / "ux_compose" / "kit"
    for path in [ROOT / "src" / "ux_compose" / "kit_construct.py", *sorted(kit_dir.glob("*.py"))]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not any(alias.name.startswith(f) for f in forbidden), path.name
            elif isinstance(node, ast.ImportFrom) and node.module:
                assert not any(node.module.startswith(f) for f in forbidden), path.name
