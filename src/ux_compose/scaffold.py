"""Progressive scaffold — create-app [--level=N|auto] [--host=auto|fastapi|asgi].

Emits the locked product path:
- routes/ with page-unit convention (module stem == class name)
- composition root: ux_compose.build(host=, live=, level=)
- Document trees + Tailwind className (no HTML strings)
- HTMX opt-in only
"""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


APP_PY = dedent('''\
    """Progressive ux-compose app (level={level_repr}, host={host}).

    Composition root: host + live set only in build().
    """
    from __future__ import annotations

    from pathlib import Path

    from ux_compose.build import build
    from ux_compose import doctor

    PACKAGE = Path(__file__).resolve().parent


    def main(*, use_htmx: bool = False):
        app, asgi, bundle = build(
            PACKAGE,
            name="{name}",
            host="{host}",
            live="auto",
            level={level_boot},
            base="routes",
            use_htmx=use_htmx,
        )
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
            print("Serve: uxcompose serve app:asgi --host 0.0.0.0 --port 8080")

    # ASGI attribute for uvicorn app:asgi
    _app, asgi, _bundle = main()
''')


ROUTES_HELLO_PY = dedent('''\
    """Page unit — module stem matches class name (hello.py → Hello).

    Author contract: return ux-dom tag trees with Tailwind className.
    control() emits semantic data-ux-* attrs. HTMX is opt-in at Document layer.
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

    Progressive ux-compose app (level={level_repr}, host={host}).

    ## Composition root

    ```python
    from ux_compose.build import build
    app, asgi, bundle = build(
        Path(__file__).parent,
        host="{host}",   # auto | fastapi | asgi
        live="auto",     # auto | channel | null
        level={level_repr_py},
    )
    ```

    ## Product path

    - `routes/hello.py` — page unit (stem == class name)
    - `render()` → ux-dom trees + Tailwind `className`
    - Host set **only** in `build(host=...)` — swap without rewriting page units

    ## Run

    ```bash
    pip install ux-compose ux-dom ux-behavior
    # optional: ux-channel ux-motion fastapi uvicorn
    python app.py
    uxcompose serve app:asgi --port 8080
    ```

    ## Laws

    - Isolation: product modules never import `ux_channel` or CEK
    - Cap Law: protected actions fail closed under `strict_caps=True`
    - HTMX is opt-in (`use_htmx=True` in main)

    ```bash
    uxcompose doctor . --no-fail
    ```
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
    (root / "README.md").write_text(
        README.format(
            name=name,
            level_repr=level_repr,
            level_repr_py=level_repr_py,
            host=host_l,
        ),
        encoding="utf-8",
    )

    routes = root / "routes"
    routes.mkdir(exist_ok=True)
    (routes / "__init__.py").write_text("", encoding="utf-8")
    (routes / "hello.py").write_text(ROUTES_HELLO_PY, encoding="utf-8")

    return root


__all__ = ["create_app"]
