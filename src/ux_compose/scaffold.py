"""Progressive scaffold — create-app [--level=N|auto].

Emits the locked product path:
- routes/ with page-unit convention (module stem == class name)
- App.mount → mount_surfaces + RouterHooks.resolve_unit
- Document trees + Tailwind className (no HTML strings)
- Default runtimes: XElement + Csp (HTMX is opt-in, not default)
- level=auto → unlock max available specialists (channel/motion when present)
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


APP_PY = dedent('''\
    """Progressive ux-compose app (level={level_repr}).

    Day-1 defaults:
    - Document trees + Tailwind className (not HTML strings)
    - XElement + Csp runtimes (HTMX is opt-in — see use_htmx below)
    - level=auto unlocks channel/motion when specialists are installed
    - Page units under routes/ via App.mount + RouterHooks

    Progressive Superpower Contract: page units stay valid across levels.
    """
    from __future__ import annotations

    from pathlib import Path

    from ux_compose import App, doctor

    try:
        from ux_dom import Document
        from ux_dom.runtime import XElement, Csp
        HAS_DOM = True
    except ImportError:
        HAS_DOM = False
        Document = XElement = Csp = None  # type: ignore

    try:
        from fastapi import FastAPI
        HAS_FASTAPI = True
    except ImportError:
        HAS_FASTAPI = False


    def build(*, use_htmx: bool = False):
        """Boot the app.

        use_htmx: opt-in HTMX control plane. Default False — stack-native
        XElement + channel (when installed) own the control path.
        """
        document = None
        if HAS_DOM:
            runtimes = [XElement(), Csp.auto()]
            if use_htmx:
                try:
                    from ux_dom.runtime import Htmx
                    runtimes.insert(1, Htmx())
                except ImportError:
                    pass
            document = Document(head=[], body=[], ensure_csrf_token=False).use(*runtimes)

        app = App.boot("{name}", strict_caps=False, level={level_boot})
        if document is not None:
            app.use_dom(document)

        if {auto_channel}:
            try:
                app.use_channel()
            except Exception:
                pass
        if {auto_motion}:
            try:
                app.use_motion()
            except Exception:
                pass

        asgi = FastAPI(title="{name}") if HAS_FASTAPI else None
        if asgi is not None and {auto_channel}:
            try:
                app.use_channel(asgi_app=asgi)
            except Exception:
                pass

        package_dir = Path(__file__).resolve().parent
        bundle = app.mount(
            package_dir,
            asgi_app=asgi,
            base="routes",
            fail_closed=True,
        )
        return app, asgi, bundle


    if __name__ == "__main__":
        app, asgi, bundle = build()
        print("Level:", int(app.level), f"({{app.level.label}})")
        print("Surfaces:", list(bundle.surfaces.keys()) if bundle else [])
        print("Routes:", [r.get("path") for r in (bundle.route_table or [])] if bundle else [])
        ops = app.dispatch("hello.inc")
        for op in ops:
            print(" ", op)
        report = doctor([], fail=False, bundle=bundle)
        print("Doctor surfaces:", report.surfaces)
        print("Doctor routes:", report.routes)
''')


ROUTES_HELLO_PY = dedent('''\
    """Page unit — module stem matches class name (hello.py → Hello).

    Author contract: return ux-dom tag trees with Tailwind className.
    control() emits semantic data-ux-* attrs (not hx_*). HTMX is opt-in
    at the Document runtime layer, not in product code.
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
            attr_str = " ".join(f'{{k}}="{{v}}"' for k, v in attrs.items())
            return (
                f'<div id="hello" class="flex items-center gap-3">'
                f"<span>{{n}}</span>"
                f"<button {{attr_str}}>+1</button>"
                f"</div>"
            )

        @action(caps=())
        def inc(self):
            self.n = int(self.n or 0) + 1
            return update_with(self, extra_ops=[notify("incremented")])
''')


README = dedent('''\
    # {name}

    Progressive ux-compose app (level={level_repr}).

    ## Product path (locked)

    - `routes/hello.py` — page unit (stem == class name)
    - `render()` returns **ux-dom trees** + Tailwind `className`
    - `app.mount(...)` — surfaces + DirectoryRouter via `RouterHooks`
    - Runtimes default: **XElement + Csp** (HTMX is opt-in)

    ## Day-1 live

    When specialists are installed, scaffold unlocks them automatically
    (`level=auto` or level ≥ 2/3). Offline L0/L1 is for tests / pins only.

    ## Opt-in HTMX

    HTMX is **not** a hard dependency. To enable:

    ```python
    app, asgi, bundle = build(use_htmx=True)
    ```

    Prefer stack-native control: `control()` / `bind()` + channel when live.

    ## Run

    ```bash
    pip install ux-compose ux-dom ux-behavior
    # optional live:
    #   pip install ux-channel ux-motion fastapi
    python app.py
    ```

    ## Laws

    - Isolation: product modules never import `ux_channel` or CEK
    - Cap Law: protected actions fail closed under `strict_caps=True`
    - Document SSoT: one Document owns the HTML shell
    - Page unit: class name matches module stem
    - Control plane: semantic `control()` attrs; HTMX is one optional consumer

    ```bash
    python -m ux_compose.cli doctor . --no-fail
    ```
''')


def create_app(
    dest: str | Path,
    *,
    name: str = "myapp",
    level: int | str = "auto",
) -> Path:
    """Create a progressive app with the locked product path (routes/ + mount).

    level:
      - "auto" (default) — unlock channel/motion when importable at runtime
      - 0..3 — pin progressive floor (tests / teaching)
    """
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)

    if isinstance(level, str) and level.lower() == "auto":
        level_repr = "auto"
        level_boot = '"auto"'
        auto_channel = "True"
        auto_motion = "True"
    else:
        lv = max(0, min(3, int(level)))
        level_repr = str(lv)
        level_boot = str(lv)
        auto_channel = "True" if lv >= 2 else "False"
        auto_motion = "True" if lv >= 3 else "False"

    (root / "app.py").write_text(
        APP_PY.format(
            name=name,
            level_repr=level_repr,
            level_boot=level_boot,
            auto_channel=auto_channel,
            auto_motion=auto_motion,
        ),
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        README.format(name=name, level_repr=level_repr),
        encoding="utf-8",
    )

    routes = root / "routes"
    routes.mkdir(exist_ok=True)
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(ROUTES_HELLO_PY, encoding="utf-8")

    return root


__all__ = ["create_app"]
