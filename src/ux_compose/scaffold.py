"""Minimal progressive scaffold — create-app --level=N."""
from __future__ import annotations

from pathlib import Path
from textwrap import dedent


APP_PY = dedent('''\
    """Progressive ux-compose app (Level {level}).

    Progressive Superpower Contract: this Level-1 Component stays valid
    when you later call use_channel() / use_motion() — zero rewrite.
    """
    from __future__ import annotations

    from ux_compose import (
        App,
        Component,
        MorphState,
        action,
        notify,
        update_with,
        control,
        doctor,
    )

    try:
        from ux_compose import scene, rise
    except Exception:
        scene = rise = None

    try:
        from ux_dom import Document
        from ux_dom.runtime import XElement, Htmx, Csp
        HAS_DOM = True
    except ImportError:
        HAS_DOM = False


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


    def build():
        document = None
        if HAS_DOM:
            document = Document(head=[], body=[], ensure_csrf_token=False).use(
                XElement(), Htmx(), Csp.auto()
            )
        app = App.boot("{name}", strict_caps=False, level={level})
        if document is not None:
            app.use_dom(document)
        # Level is progressive: use_* is additive and safe when specialists absent
        if {level} >= 2:
            app.use_channel()
        if {level} >= 3:
            app.use_motion()
        app.add(Hello)
        return app


    if __name__ == "__main__":
        app = build()
        print("Level:", int(app.level), f"({{app.level.label}})")
        ops = app.dispatch("hello.inc")
        for op in ops:
            print(" ", op)
        report = doctor([], fail=False)
        print("Doctor capabilities:", report.capabilities)
''')

README = dedent('''\
    # {name}

    Progressive ux-compose app scaffolded at **Level {level}**.

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
    #   ux-dom       → Document SSoT (Python ≥3.14)
    python app.py
    ```

    ## Laws

    - Isolation: product modules never import `ux_channel` or CEK
    - Cap Law: protected actions fail closed offline under `strict_caps=True`
    - Document SSoT: one Document owns the HTML shell
    - Morph-then-Play: morph Op before `transition.play`

    ```bash
    python -m ux_compose.cli doctor . --no-fail
    ```
''')


def create_app(dest: str | Path, *, name: str = "myapp", level: int = 1) -> Path:
    """Create a minimal progressive app directory."""
    root = Path(dest)
    root.mkdir(parents=True, exist_ok=True)
    level = max(0, min(3, int(level)))
    (root / "app.py").write_text(APP_PY.format(name=name, level=level), encoding="utf-8")
    (root / "README.md").write_text(README.format(name=name, level=level), encoding="utf-8")
    return root


__all__ = ["create_app"]
