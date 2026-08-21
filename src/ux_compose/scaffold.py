"""Progressive scaffold — create-app --level=N.

Emits the locked product path:
- routes/ with page-unit convention (module stem == class name)
- App.mount → mount_surfaces + RouterHooks.resolve_unit
- Progressive Levels 0–3 still work (use_channel / use_motion)
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


APP_PY = dedent('''\
    """Progressive ux-compose app (Level {level}).

    Progressive Superpower Contract: this Level-1 page unit stays valid
    when you later call use_channel() / use_motion() — zero rewrite.

    Product path:
    - routes/hello.py  → page unit (stem match)
    - app.mount(...)   → mount_surfaces + DirectoryRouter via RouterHooks
    """
    from __future__ import annotations

    from pathlib import Path

    from ux_compose import (
        App,
        doctor,
    )

    try:
        from ux_dom import Document
        from ux_dom.runtime import XElement, Htmx, Csp
        HAS_DOM = True
    except ImportError:
        HAS_DOM = False

    try:
        from fastapi import FastAPI
        HAS_FASTAPI = True
    except ImportError:
        HAS_FASTAPI = False


    def build():
        document = None
        if HAS_DOM:
            document = Document(head=[], body=[], ensure_csrf_token=False).use(
                XElement(), Htmx(), Csp.auto()
            )

        app = App.boot("{name}", strict_caps=False, level={level})
        if document is not None:
            app.use_dom(document)

        # Progressive unlocks (additive, safe when specialists absent)
        if {level} >= 2:
            app.use_channel()
        if {level} >= 3:
            app.use_motion()

        # Optional ASGI so DirectoryRouter can mount
        asgi = None
        if HAS_FASTAPI:
            asgi = FastAPI(title="{name}")

        # Locked product path: page units under routes/ + RouterHooks
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
        # Offline dispatch still works
        ops = app.dispatch("hello.inc")
        for op in ops:
            print(" ", op)
        report = doctor([], fail=False)
        print("Doctor capabilities:", report.capabilities)
''')


ROUTES_HELLO_PY = dedent('''\
    """Page unit — module stem matches class name (hello.py → Hello).

    This is the default product path used by DirectoryRouter + mount_surfaces.
    """
    from __future__ import annotations

    from ux_compose import (
        Component,
        MorphState,
        action,
        notify,
        update_with,
        control,
    )

    try:
        from ux_compose import scene, rise
    except Exception:
        scene = rise = None


    class Hello(Component):
        id = "hello"
        n = MorphState(0)

        def render(self):
            attrs = control("inc")
            attr_str = " ".join(f'{{k}}="{{v}}"' for k, v in attrs.items())
            return (
                f'<div id="hello">'
                f'<span>{{self.n}}</span>'
                f'<button {{attr_str}}>+1</button>'
                f'</div>'
            )

        @action(caps=())
        def inc(self):
            self.n = int(self.n) + 1
            plan = None
            if scene is not None and rise is not None:
                try:
                    plan = scene("inc").enter("#hello", rise.enter(ms=100))
                except Exception:
                    plan = None
            return update_with(self, plan, extra_ops=[notify("incremented")])
''')


README = dedent('''\
    # {name}

    Progressive ux-compose app scaffolded at **Level {level}**.

    ## Product path (locked)

    - `routes/hello.py` — page unit (module stem == class name)
    - `app.mount(...)` — `mount_surfaces` + DirectoryRouter via generic `RouterHooks`
    - Progressive Levels still work: code written at Level 1 stays valid at L2/L3

    ## Progressive Superpower Contract

    Code written at Level 1 remains correct and unchanged when you unlock
    Channel (Level 2) or Motion (Level 3). Zero rewrite.

    ## Run

    ```bash
    pip install ux-compose
    # optional specialists:
    #   ux-behavior  → L1 interactive
    #   ux-channel   → L2 live Caps
    #   ux-motion    → L3 choreography
    #   ux-dom       → Document SSoT + DirectoryRouter (Python ≥3.14)
    #   fastapi      → ASGI host for the router
    python app.py
    ```

    ## Laws

    - Isolation: product modules never import `ux_channel` or CEK
    - Cap Law: protected actions fail closed offline under `strict_caps=True`
    - Document SSoT: one Document owns the HTML shell
    - Page unit: class name matches module stem (`hello.py` → `Hello`)
    - Morph-then-Play: morph Op before `transition.play`

    ```bash
    python -m ux_compose.cli doctor . --no-fail
    ```
''')


def create_app(dest: str | Path, *, name: str = "myapp", level: int = 1) -> Path:
    """Create a progressive app with the locked product path (routes/ + mount)."""
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)
    level = max(0, min(3, int(level)))

    (root / "app.py").write_text(APP_PY.format(name=name, level=level), encoding="utf-8")
    (root / "README.md").write_text(README.format(name=name, level=level), encoding="utf-8")

    routes = root / "routes"
    routes.mkdir(exist_ok=True)
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(ROUTES_HELLO_PY, encoding="utf-8")

    return root


__all__ = ["create_app"]
