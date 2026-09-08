"""Progressive scaffold — create-app [--level=N|auto] [--host=auto|fastapi|asgi].

Emits the locked product path:

- settings.py          environment SSoT (BASE_DIR, DEBUG, WebAssets)
- document.py          Document SSoT + .use(XElement, Csp, Channel.optional)
- app.py               composition root via build(host=, live=, level=, document=, cek=)
- routes/index.py      GET / alias so the app root is not 404
- routes/hello.py      page unit (module stem == class name)
- assets/css/input.css Tailwind tokens + @source
- requirements.txt     so ``uxcompose deploy`` is not a lie

Laws: Isolation (no ux_channel in product files). Progressive Superpower
(complete install first; Level 1 page units stay correct when Channel or
Motion attach).
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


APP_PY = dedent('''\
    """Progressive ux-compose app (level={level_repr}, host={host}).

    Composition root: host + live set only in build().
    Document SSoT lives in document.py.
    Environment in settings.py.
    """
    from __future__ import annotations

    from pathlib import Path

    from ux_compose.build import build
    from ux_compose import doctor
    {chrome_import}from document import document
    from settings import webassets

    PACKAGE = Path(__file__).resolve().parent


    def _mount_css(asgi):
        """Serve compiled CSS at /css/output.css. Returns asgi (maybe wrapped)."""
        if asgi is None or webassets is None:
            return asgi
        mount = getattr(webassets, "mount_css", None)
        if callable(mount):
            return mount(asgi)
        css_dir = getattr(getattr(webassets, "static", None), "css", None)
        if css_dir is None:
            return asgi
        from pathlib import Path as _P
        from starlette.staticfiles import StaticFiles

        _P(str(css_dir)).mkdir(parents=True, exist_ok=True)
        asgi.mount(
            "/css",
            StaticFiles(directory=str(css_dir), check_dir=False),
            name="css",
        )
        return asgi


    def main(*, use_htmx: bool = False):
        app, asgi, bundle = build(
            PACKAGE,
            name="{name}",
            host="{host}",
            live="auto",
            level={level_boot},
            base="routes",
            use_htmx=use_htmx,
            document=document,
            wrap={wrap_expr},
            cek="require",
        )
        asgi = _mount_css(asgi)
        return app, asgi, bundle


    if __name__ == "__main__":
        app, asgi, bundle = main()
        print("Level:", int(app.level), f"({{app.level.label}})")
        print("Host ASGI:", type(asgi).__name__ if asgi is not None else None)
        print("Surfaces:", list(bundle.surfaces.keys()) if bundle else [])
        print("Routes:", [r.get("path") for r in (bundle.route_table or [])] if bundle else [])
        try:
            ops = app.dispatch("hello.inc")
            for op in ops:
                print(" ", op)
        except Exception as exc:
            print(" dispatch:", exc)
        report = doctor([], fail=False, bundle=bundle, app=app)
        print("Doctor surfaces:", report.surfaces)
        print("Doctor routes:", report.routes)
        if asgi is not None:
            print("Path: uxcompose serve dev")

    # ASGI attribute for uvicorn app:asgi
    _app, asgi, _bundle = main()
''')


SETTINGS_PY = dedent('''\
    """Environment SSoT — paths, debug, app asset layout.

    Document emits ``<link href=\"/css/output.css\">``. This module owns the
    disk folders. Isolation Law: Channel stays behind compose wire/.
    """
    from __future__ import annotations

    import os
    from pathlib import Path

    from ux_compose import WebAssets

    BASE_DIR = Path(__file__).resolve().parent
    DEBUG = os.environ.get("DEBUG", "1") not in ("0", "false", "False")

    ASSETS_DIR = BASE_DIR / "assets"
    OUTPUT_CSS = "output.css"

    # dry_run=False creates assets/static/file/css (compiler output dir)
    webassets = WebAssets(base_dir=ASSETS_DIR, dry_run=False)
''')


DOCUMENT_PY = dedent('''\
    """Document SSoT — one HTML shell for every GET.

    Document.use(XElement(), Csp.auto(), Channel.optional()) is the full
    shell (CSP + Channel client tags). Channel is the ux_dom.runtime
    alias — never ux_channel.Channel. Isolation: this module never imports
    ux_channel.

    HTMX is opt-in via build(use_htmx=True). Component.render() stays a
    fragment (the morph payload) — never put the stylesheet link inside render().
    """
    from __future__ import annotations

    from ux_dom import Document
    from ux_dom.runtime import XElement, Csp, Channel
    from ux_dom.dom import link, meta, title

    from settings import OUTPUT_CSS

    _plugins = (XElement(), Csp.auto(), Channel.optional())
    document = Document(
        head=[
            meta(charset="utf-8"),
            meta(name="viewport", content="width=device-width, initial-scale=1"),
            title("Hello"),
            link(href=f"/css/{OUTPUT_CSS}", rel="stylesheet"),
        ],
        body=[],
        ensure_csrf_token=False,
    ).use(*[p for p in _plugins if p is not None])
''')


ROUTES_HELLO_PY = dedent('''\
    """Page unit — module stem matches class name (hello.py → Hello).

    Author contract: return ux-dom tag trees with Tailwind className.
    control() emits data-ux-action + data-channel-action (live click bind)
    and mints a Cap when Cap Host is live. hello.inc is open mint / no Cap
    predicate (Intent still requires the control-minted cap under Cap Host
    require). hello.pulse is fail-closed (caps=("pulse",)). HTMX is opt-in at
    Document layer. render() stays a #hello fragment (the morph payload).
    Host wraps Document — never chrome inside render().
    """
    from __future__ import annotations

    from ux_compose import Component, MorphState, action, control, notify, update_with
    from ux_compose import div, span, button


    class Hello(Component):
        id = "hello"
        n = MorphState(0)
        pulses = MorphState(0)

        def render(self):
            n = int(self.n or 0)
            pulses = int(self.pulses or 0)
            inc_attrs = control("hello.inc")
            pulse_attrs = control("hello.pulse")
            btn = (
                "rounded-full bg-stone-900 text-stone-50 "
                "px-4 py-2 text-sm font-medium hover:bg-stone-800"
            )
            return div(
                span(str(n), className="text-2xl font-semibold tabular-nums"),
                button("+1", type="button", className=btn, **inc_attrs),
                span(str(pulses), className="text-2xl font-semibold tabular-nums"),
                button("pulse", type="button", className=btn, **pulse_attrs),
                id=self.id,
                className="flex items-center gap-3 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm",
            )

        @action(caps=())
        def inc(self):
            self.n = int(self.n or 0) + 1
            return update_with(self, extra_ops=[notify("incremented")])

        @action(caps=("pulse",))
        def pulse(self):
            self.pulses = int(self.pulses or 0) + 1
            return update_with(self, extra_ops=[notify("pulsed")])
''')


ROUTES_INDEX_PY = dedent('''\
    """Page unit — index.py → GET /. Keep /hello; the app root is not 404.

    Path law: index.py / route.py map to the folder prefix (here ``/``).
    Isolation: this module never imports ux_channel.
    """
    from __future__ import annotations

    from ux_compose import Component, a, div, p


    class Index(Component):
        id = "index"

        def render(self):
            href = "/hello"
            return div(
                p("Hello lives at /hello."),
                a("Open hello", href=href),
                id=self.id,
                className="flex flex-col gap-2 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm",
            )
''')


INPUT_CSS = dedent('''\
    @import "tailwindcss";
    @source "../../**/*.{py,html,js}";

    @layer base {
      :root {
        --bg: #f3efe6;
        --surface: #fffdf8;
        --fg: #161513;
        --accent: #2f3b38;
        --font-display: "Fraunces", Georgia, serif;
        --font-body: "Source Sans 3", system-ui, sans-serif;
      }
      html { background: var(--bg); color: var(--fg); }
      body { margin: 0; font-family: var(--font-body); }
    }

    @layer components {
    }
''')


# Pins match Makefile / pyproject.toml (SSOT). CI installs via pip install -e ".[dev]".
CHANNEL_VCS_PIN = "31a60bdd40a1b52aea1fd13159ad09c293c63fd6"
BEHAVIOR_VCS_PIN = "793f120e3b1388925772cd069b070d7918b78baa"
MOTION_VCS_PIN = "67ff3f0c4912b70b7056f8226a6f226b6fe93f60"
DOM_VCS_PIN = "e8be99a52bfecd6026c200fa1c3dc6a74f87aacb"
COMPOSE_VCS_PIN = "6d61c9e616652d996e55a36886ccfec218308c30"

REQUIREMENTS = dedent(f'''\
    ux-compose @ git+https://github.com/bitplorer/ux-compose.git@{COMPOSE_VCS_PIN}
    ux-dom @ git+https://github.com/bitplorer/ux-dom.git@{DOM_VCS_PIN}
    ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git@{BEHAVIOR_VCS_PIN}
    ux-motion @ git+https://github.com/bitplorer/ux-motion.git@{MOTION_VCS_PIN}
    ux-channel @ git+https://github.com/bitplorer/ux-channel.git@{CHANNEL_VCS_PIN}#subdirectory=python
    cek-host>=0.1.3
    cek-surface>=0.1.3
    fastapi
    uvicorn[standard]
''')


README = dedent('''\
    # {name}

    Progressive ux-compose app (level={level_repr}, host={host}).

    ## Mental model

    - `settings.py` — environment (BASE_DIR, DEBUG, WebAssets on ux-compose)
    - `document.py` — Document SSoT + `.use(XElement, Csp, Channel.optional)`
    - `app.py` — composition root: `build(host=, live=, level=, document=, wrap=, cek=)`
    - `routes/index.py` — GET `/` (index alias; keep `/hello`)
    - `routes/hello.py` — page unit (`render()` is a fragment; host wraps Document)
    - `assets/css/input.css` — Tailwind tokens; compile with `uxcompose build`

    ## Composition root

    ```python
    from ux_compose.build import build
    {readme_chrome_import}from document import document
    app, asgi, bundle = build(
        Path(__file__).parent,
        host="{host}",   # auto | fastapi | asgi
        live="auto",     # auto | channel | null
        level={level_repr_py},
        document=document,
        wrap={wrap_expr},
        cek="require",   # product Cap Host via App.use_cek (skip if live=null)
    )
    ```

    Host is set **only** in `build(host=...)` — swap without rewriting page units.

    GET brand chrome (optional): `wrap=brand_wrap(document, brand="Acme")`
    from `ux_compose.chrome`. Keep `render()` a fragment — never put nav brand
    inside `routes/*.py`.

    ## Product path

    One Product. Python ≥ 3.14 with the pinned specialist stack.
    `pip install -r requirements.txt` is enough.

    Isolation: never import `ux_channel`.

    ```bash
    pip install -r requirements.txt
    uxcompose serve dev
    uxcompose build
    uxcompose serve prod
    uxcompose deploy --provider docker
    uxcompose doctor .
    ```

    `uxcompose build` finds and runs the Tailwind CLI (`ux_compose.tailwind`).
    Output: `assets/static/file/css/output.css`, linked as `/css/output.css`.

    ## Laws

    - Isolation: product modules never import `ux_channel` or CEK
    - Cap Law: protected actions fail closed under `strict_caps=True`
    - HTMX is opt-in (`use_htmx=True` in main)
    - Progressive Superpower: complete install first; this Level 1 page unit
      stays correct at L2/L3 (levels are additive)
''')


def create_app(
    dest: str | Path,
    *,
    name: str = "myapp",
    level: int | str = "auto",
    host: str = "auto",
    brand: str | None = None,
) -> Path:
    """Create a progressive app with locked product path.

    host: ``auto`` | ``fastapi`` | ``asgi`` — gateway at composition root only.
    level: ``auto`` or 0..3 attach level (complete install; hard-deps).
    brand: optional GET-only nav label via ``brand_wrap`` (Document path).
      ``None`` keeps ``wrap=document``. Never embeds chrome in ``render()``.
    """
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)

    host_l = (host or "auto").lower()
    if host_l not in ("auto", "fastapi", "asgi"):
        host_l = "auto"

    if isinstance(level, str) and level.lower() == "auto":
        level_repr = "auto"
        level_boot = '"auto"'
        level_repr_py = '"auto"'
    else:
        lv = max(0, min(3, int(level)))
        level_repr = str(lv)
        level_boot = str(lv)
        level_repr_py = str(lv)

    brand_label = str(brand).strip() if brand else ""
    if brand_label:
        chrome_import = "from ux_compose.chrome import brand_wrap\n"
        wrap_expr = f"brand_wrap(document, brand={brand_label!r})"
        readme_chrome_import = "from ux_compose.chrome import brand_wrap\n"
    else:
        chrome_import = ""
        wrap_expr = "document"
        readme_chrome_import = ""

    (root / "app.py").write_text(
        APP_PY.format(
            name=name,
            level_repr=level_repr,
            level_boot=level_boot,
            host=host_l,
            chrome_import=chrome_import,
            wrap_expr=wrap_expr,
        ),
        encoding="utf-8",
    )
    (root / "settings.py").write_text(SETTINGS_PY, encoding="utf-8")
    (root / "document.py").write_text(DOCUMENT_PY, encoding="utf-8")
    (root / "README.md").write_text(
        README.format(
            name=name,
            level_repr=level_repr,
            level_repr_py=level_repr_py,
            host=host_l,
            wrap_expr=wrap_expr,
            readme_chrome_import=readme_chrome_import,
        ),
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")

    routes = root / "routes"
    routes.mkdir(exist_ok=True)
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "index.py").write_text(ROUTES_INDEX_PY, encoding="utf-8")
    (routes / "hello.py").write_text(ROUTES_HELLO_PY, encoding="utf-8")

    css_dir = root / "assets" / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    (css_dir / "input.css").write_text(INPUT_CSS, encoding="utf-8")
    from ux_compose.assets import WebAssets

    WebAssets.from_app_root(root, dry_run=False)

    return root


__all__ = ["create_app"]
