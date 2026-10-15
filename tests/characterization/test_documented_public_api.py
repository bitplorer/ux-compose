"""Characterization of the documented public API.

Pins the usage in START_HERE, docs/guides/SNIPPETS.md, and examples
(cart, foundation, live_caps). Does not lock side effects that are not
part of that contract.
"""
from __future__ import annotations

import json

import pytest
from ux_behavior import AuthorityError

from tests.asgi_http import asgi_http
from ux_compose import (
    App,
    Component,
    Level,
    MorphState,
    RefState,
    WebAssets,
    act,
    action,
    bind,
    button,
    control,
    div,
    doctor,
    field,
    h1,
    mark_dirty,
    notify,
    optional_plan,
    scene,
    status,
    rise,
    update_with,
)
from ux_compose.build import build
from ux_compose.routing import DirectoryRoutes
from ux_compose.routing.host import ProductBatteriesRejected, open as host_open
from ux_compose.scaffold import create_app
from ux_compose.surfaces import SurfaceError, mount_surfaces, scan_surfaces, validate_surfaces
from ux_dom.response.serialize import to_html_bytes


def _html(tree) -> str:
    return to_html_bytes(tree).decode("utf-8")


def _op_name(op) -> str:
    if isinstance(op, dict):
        return str(op.get("op") or "")
    return str(getattr(op, "name", "") or "")


def _payload(op) -> dict:
    if isinstance(op, dict):
        return op
    return dict(getattr(op, "payload", None) or {})


class Cart(Component):
    """START_HERE / SNIPPETS Level-1 cart."""

    id = "cart"
    count = MorphState(0)

    def render(self):
        return div(
            h1(f"Items: {self.count}"),
            button("+ tee", **control("add", sku="tee")),
            button("+ hat", **bind(self.add, sku="hat")),
            id=self.id,
        )

    @action(caps=())
    def add(self, sku: str = ""):
        self.count = int(self.count) + 1
        return update_with(self, extra_ops=[notify(f"Added {sku}")])

    @action(caps=("orders.place",))
    def checkout(self):
        return [notify("Checkout started")]


def test_level1_cart_dispatch_matches_start_here():
    app = App.boot("Shop", strict_caps=False, level=1)
    app.add(Cart)
    assert int(app.level) == 1
    assert app.level.label == "offline interactive"

    ops = app.dispatch("cart.add", sku="tee")
    inst = app.behavior.get("cart")
    assert int(inst.count) == 1
    assert any(_op_name(op) == "morph" and "Items: 1" in str(_payload(op)) for op in ops)
    assert any("Added tee" in str(_payload(op)) for op in ops)

    page = _html(inst.render())
    assert 'data-ux-action="add"' in page
    assert 'data-channel-action="add"' in page
    assert "Items: 1" in page


def test_bind_uses_method_name_and_control_keeps_the_string():
    app = App.boot("Shop", strict_caps=False, level=1)
    app.add(Cart)
    inst = app.behavior.get("cart")

    via_control = control("add", sku="tee")
    via_bind = bind(inst.add, sku="hat")

    assert via_control["data-ux-action"] == "add"
    assert via_control["data-channel-action"] == "add"
    assert json.loads(via_control["data-channel-args"]) == {"sku": "tee"}
    assert via_control["data-ux-arg-sku"] == "tee"

    assert via_bind["data-ux-action"] == "cart.add"
    assert via_bind["data-channel-action"] == "cart.add"
    assert json.loads(via_bind["data-channel-args"]) == {"sku": "hat"}


def test_strict_caps_refuses_protected_action_and_allows_open_mint():
    app = App.boot("Shop", strict_caps=True)
    app.add(Cart)
    with pytest.raises(AuthorityError):
        app.dispatch("cart.checkout")

    ops = app.dispatch("cart.add", sku="tee")
    assert int(app.behavior.get("cart").count) == 1
    assert any("Added tee" in str(_payload(op)) for op in ops)


def test_doctor_reports_the_fields_examples_print():
    report = doctor([], fail=False)
    assert report.ok is True
    assert report.level_available == 3
    assert report.capabilities["ux_dom"] is True
    assert report.capabilities["ux_behavior"] is True
    assert report.capabilities["directory_routes"] is True
    assert isinstance(report.diagnostics, list)
    assert isinstance(report.teaching, list)


def test_level_labels_match_the_progressive_contract():
    assert [int(level) for level in Level] == [0, 1, 2, 3]
    assert Level.L0.label == "static + routing"
    assert Level.L1.label == "offline interactive"
    assert Level.L2.label == "live channel"
    assert Level.L3.label == "motion"


def test_use_cek_rejects_unknown_mode_and_off_stays_offline():
    app = App.boot("Shop", level=1)
    with pytest.raises(ValueError, match="off, adapt, or require"):
        app.use_cek(mode="banana")

    off = App.boot("Shop", level=1)
    off.use_cek(mode="off")
    assert int(off.level) == 1
    assert off.level.label == "offline interactive"


def test_update_with_morphs_live_render_and_keeps_html_off_the_plan():
    app = App.boot("Shop", strict_caps=False, level=1)

    class Box(Component):
        id = "box"
        n = MorphState(0)

        def render(self):
            return div(f"n={int(self.n)}", id=self.id)

        @action(caps=())
        def inc(self):
            self.n = int(self.n) + 1
            plan = scene("box-pop").enter(f"#{self.id}", rise.enter(ms=160))
            return update_with(self, plan, extra_ops=[notify("pop")])

    app.add(Box)
    ops = app.dispatch("box.inc")
    morphs = [op for op in ops if _op_name(op) == "morph"]
    plays = [op for op in ops if _op_name(op) == "play"]
    assert morphs and "n=1" in str(_payload(morphs[0]))
    assert plays
    plan = _payload(plays[0]).get("plan")
    assert isinstance(plan, dict)
    assert plan.get("id") == "box-pop"
    assert "html" not in plan
    assert any("pop" in str(_payload(op)) for op in ops)


def test_author_helpers_match_example_forms():
    tree = act("counter.inc", "Increase", kind="primary", sku="tick")
    html = _html(tree)
    assert 'action="/act/counter.inc"' in html
    assert 'method="post"' in html
    assert 'name="sku"' in html and 'value="tick"' in html
    assert 'data-ux-action="counter.inc"' in html
    assert 'class="btn-primary"' in html

    assert 'value="x&lt;y"' in _html(field("secret", "x<y", placeholder="Passphrase"))
    quiet = _html(status(""))
    assert "sr" in quiet
    assert "status-note" not in quiet
    saved = _html(status("saved"))
    assert 'role="status"' in saved
    assert "saved" in saved


def test_mark_dirty_flips_the_qualitative_flag_foundation_uses():
    class Planes(Component):
        id = "planes"
        shown = MorphState("hello")
        silent = RefState(0)
        dirty = MorphState("idle")

        def render(self):
            return div(id=self.id)

        @action(caps=())
        def ref_and_mark_dirty(self):
            self.silent = int(self.silent or 0) + 1
            mark_dirty(self)
            return update_with(self, optional_plan("planes", f"#{self.id}"))

    app = App.boot("Foundation", strict_caps=False, level=1)
    app.add(Planes)
    app.dispatch("planes.ref_and_mark_dirty")
    inst = app.behavior.get("planes")
    assert int(inst.silent) == 1
    assert str(inst.dirty) in {"tick", "tock"}


def test_same_cart_still_dispatches_after_motion_attach():
    app = App.boot("Shop", strict_caps=False, level=1)
    app.add(Cart)
    app.use_motion()
    assert int(app.level) == 3
    app.dispatch("cart.add", sku="tee")
    assert int(app.behavior.get("cart").count) == 1


def test_webassets_layout_matches_the_css_contract():
    assets = WebAssets(base_dir="assets", dry_run=True)
    assert assets.css_href == "/css/output.css"
    assert assets.output_css.name == "output.css"
    assert assets.output_css.parts[-4:] == ("static", "file", "css", "output.css")
    assert assets.input_css.parts[-2:] == ("css", "input.css")


def test_create_app_build_serves_hello_fragment(tmp_path):
    """Product path: create-app, then build(document=, wrap=document)."""
    from ux_dom import Document

    root = create_app(tmp_path / "myapp", name="Shop", level=1, host="asgi")
    document = Document(head=[], body=[], ensure_csrf_token=False)
    app, asgi, bundle = build(
        root,
        name="Shop",
        host="asgi",
        live="null",
        level=1,
        document=document,
        wrap=document,
        cek="off",
    )
    assert app.name == "Shop"
    assert int(app.level) == 1
    assert app.level.label == "offline interactive"
    paths = [row["path"] for row in bundle.route_table]
    assert "/" in paths
    assert "/hello" in paths

    status_code, _headers, body = asgi_http(asgi, "/hello")
    text = body.decode("utf-8")
    assert status_code == 200
    assert 'id="hello"' in text
    assert "<html" in text.lower()

    status_code, _headers, _body = asgi_http(asgi, "/")
    assert status_code == 200

    ops = app.dispatch("hello.inc")
    assert any(_op_name(op) == "morph" for op in ops)


def test_scan_validate_mount_one_page_per_file(tmp_path):
    routes = tmp_path / "routes"
    routes.mkdir()
    (routes / "hello.py").write_text(
        "from ux_compose import Component\n"
        "class Hello(Component):\n"
        "    id = 'hello'\n"
        "    def render(self):\n"
        "        return 'hi'\n",
        encoding="utf-8",
    )
    found = scan_surfaces(tmp_path, base_directory="routes")
    validate_surfaces(found)
    assert len(found) == 1
    assert found[0].id == "hello"
    assert found[0].is_page is True
    assert found[0].url_path == "/hello"

    app = App.boot("Shop", level=1)
    bundle = mount_surfaces(
        package_dir=tmp_path,
        base_directory="routes",
        compose_app=app,
        fail_closed=True,
        bind_pages=False,
    )
    assert "hello" in bundle.surfaces
    assert bundle.errors == []


def test_validate_surfaces_rejects_duplicate_ids(tmp_path):
    routes = tmp_path / "routes"
    routes.mkdir()
    (routes / "one.py").write_text(
        "from ux_compose import Component\n"
        "class One(Component):\n"
        "    id = 'same'\n"
        "    def render(self):\n"
        "        return 'a'\n",
        encoding="utf-8",
    )
    (routes / "two.py").write_text(
        "from ux_compose import Component\n"
        "class Two(Component):\n"
        "    id = 'same'\n"
        "    def render(self):\n"
        "        return 'b'\n",
        encoding="utf-8",
    )
    found = scan_surfaces(tmp_path, base_directory="routes")
    with pytest.raises(SurfaceError, match="duplicate surface id"):
        validate_surfaces(found)


def test_directory_routes_path_law(tmp_path):
    """index → /, stem → /stem, [sku] → /{sku}. Class name is not in the path."""
    routes = tmp_path / "routes"
    (routes / "shop").mkdir(parents=True)
    (routes / "item").mkdir()
    page = (
        "from ux_compose import Component\n"
        "class {cls}(Component):\n"
        "    id = '{id}'\n"
        "    def render(self):\n"
        "        return 'x'\n"
    )
    (routes / "index.py").write_text(page.format(cls="Index", id="index"), encoding="utf-8")
    (routes / "hello.py").write_text(page.format(cls="Hello", id="hello"), encoding="utf-8")
    (routes / "shop" / "index.py").write_text(
        page.format(cls="Index", id="shop"), encoding="utf-8"
    )
    (routes / "item" / "[sku].py").write_text(
        page.format(cls="Sku", id="sku"), encoding="utf-8"
    )
    core = DirectoryRoutes(tmp_path, base_directory="routes")
    core.discover()
    paths = {rec.path for rec in core.records}
    assert paths == {"/", "/hello", "/shop", "/item/{sku}"}


def test_host_batteries_fails_closed():
    with pytest.raises(ProductBatteriesRejected):
        host_open(name="Shop", host="batteries")


def test_public_tags_escape_text():
    html = _html(h1('a<b>"c'))
    assert "a&lt;b&gt;" in html
    assert "<b>" not in html
