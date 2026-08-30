"""Progressive scaffold — create-app [--level=N|auto] [--host=auto|fastapi|asgi].

Emits the locked product path:

- settings.py          environment SSoT (BASE_DIR, DEBUG, WebAssets)
- document.py          Document SSoT + .use(XElement, Csp)
- app.py               composition root via build(host=, live=, level=, document=)
- routes/hello.py      page unit (module stem == class name)
- assets/css/input.css Tailwind tokens + @source
- requirements.txt     so ``uxcompose deploy`` is not a lie

Laws: Isolation (no ux_channel in product files). Progressive Superpower
(Level 1 page units stay correct when Channel or Motion unlock).
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


APP_PY = dedent('''\
    """Progressive ux-compose app (level={level_repr}, host={host}).

    Composition root: host + live set only in build().
    Document SSoT lives in document.py; environment in settings.py.
    """
    from __future__ import annotations

    from pathlib import Path

    from ux_compose.build import build
    from ux_compose import doctor

    PACKAGE = Path(__file__).resolve().parent

    try:
        from document import document
    except Exception:
        document = None
    try:
        from settings import webassets
    except Exception:
        webassets = None


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
        report = doctor([], fail=False, bundle=bundle)
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

    .use(XElement, Csp) attaches runtimes. HTMX is opt-in via build(use_htmx=True).
    The host wraps render() with this Document. Component.render() stays a
    fragment (the morph payload) — never put the stylesheet link inside render().
    Isolation: this module never imports ux_channel.
    """
    from __future__ import annotations

    try:
        from ux_dom import Document
        from ux_dom.runtime import XElement, Csp
        from ux_dom.dom import link, meta, title

        from settings import OUTPUT_CSS

        document = Document(
            head=[
                meta(charset="utf-8"),
                meta(name="viewport", content="width=device-width, initial-scale=1"),
                title("Hello"),
                link(href=f"/css/{OUTPUT_CSS}", rel="stylesheet"),
            ],
            body=[],
            ensure_csrf_token=False,
        ).use(XElement(), Csp.auto())

    except Exception:  # ux-dom not installed — L1 HTML-string fallback still works
        document = None
''')


ROUTES_HELLO_PY = dedent('''\
    """Page unit — module stem matches class name (hello.py → Hello).

    Author contract: return ux-dom tag trees with Tailwind className.
    control() emits semantic data-ux-* attrs. HTMX is opt-in at Document layer.
    render() stays a fragment (the morph payload). The host wraps Document.
    """
    from __future__ import annotations

    from ux_compose import Component, MorphState, action, control, notify, update_with

    try:
        from ux_compose import div, span, button, HAS_DOM
    except Exception:
        HAS_DOM = False
        div = span = button = None  # type: ignore


    class Hello(Component):
        id = "hello"
        n = MorphState(0)

        def render(self):
            n = int(self.n or 0)
            attrs = control("hello.inc")
            if HAS_DOM and div is not None:
                return div(
                    span(str(n), className="text-2xl font-semibold tabular-nums"),
                    button(
                        "+1",
                        type="button",
                        className=(
                            "rounded-full bg-stone-900 text-stone-50 "
                            "px-4 py-2 text-sm font-medium hover:bg-stone-800"
                        ),
                        **attrs,
                    ),
                    id=self.id,
                    className="flex items-center gap-3 rounded-2xl border border-stone-200 bg-white p-6 shadow-sm",
                )
            attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
            return (
                f'<div id="hello" class="flex items-center gap-3">'
                f"<span>{n}</span>"
                f"<button {attr_str}>+1</button>"
                f"</div>"
            )

        @action(caps=())
        def inc(self):
            self.n = int(self.n or 0) + 1
            return update_with(self, extra_ops=[notify("incremented")])
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


REQUIREMENTS = dedent('''\
    ux-compose
    ux-dom
    ux-behavior
    fastapi
    uvicorn[standard]
''')


README = dedent('''\
    # {name}

    Progressive ux-compose app (level={level_repr}, host={host}).

    ## Mental model

    - `settings.py` — environment (BASE_DIR, DEBUG, WebAssets on ux-compose)
    - `document.py` — Document SSoT + `.use(XElement, Csp)`; host wraps GET
    - `app.py` — composition root: `build(host=, live=, level=, document=)`
    - `routes/hello.py` — page unit (`render()` is a fragment; host wraps Document)
    - `assets/css/input.css` — Tailwind tokens; compile with `uxcompose build`

    ## Composition root

    ```python
    from ux_compose.build import build
    from document import document
    app, asgi, bundle = build(
        Path(__file__).parent,
        host="{host}",   # auto | fastapi | asgi
        live="auto",     # auto | channel | null
        level={level_repr_py},
        document=document,
    )
    ```

    Host is set **only** in `build(host=...)` — swap without rewriting page units.

    ## Product path

    ```bash
    pip install -r requirements.txt
    uxcompose serve dev
    uxcompose build
    uxcompose serve prod
    uxcompose deploy --provider docker
    uxcompose doctor . --no-fail
    ```

    `uxcompose build` finds and runs the Tailwind CLI (`ux_compose.tailwind`).
    Output: `assets/static/file/css/output.css`, linked as `/css/output.css`.

    ## Laws

    - Isolation: product modules never import `ux_channel` or CEK
    - Cap Law: protected actions fail closed under `strict_caps=True`
    - HTMX is opt-in (`use_htmx=True` in main)
    - Progressive Superpower: this Level 1 page unit stays correct at L2/L3
''')


def create_app(
    dest: str | Path,
    *,
    name: str = "myapp",
    level: int | str = "auto",
    host: str = "auto",
) -> Path:
    """Create a progressive app with locked product path.

    host: ``auto`` | ``fastapi`` | ``asgi`` — gateway at composition root only.
    level: ``auto`` or 0..3 progressive floor.
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

    (root / "app.py").write_text(
        APP_PY.format(
            name=name,
            level_repr=level_repr,
            level_boot=level_boot,
            host=host_l,
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
        ),
        encoding="utf-8",
    )
    (root / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")

    routes = root / "routes"
    routes.mkdir(exist_ok=True)
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(ROUTES_HELLO_PY, encoding="utf-8")

    css_dir = root / "assets" / "css"
    css_dir.mkdir(parents=True, exist_ok=True)
    (css_dir / "input.css").write_text(INPUT_CSS, encoding="utf-8")
    from ux_compose.assets import WebAssets

    WebAssets.from_app_root(root, dry_run=False)

    return root


__all__ = ["create_app"]
