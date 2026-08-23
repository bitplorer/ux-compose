"""Page unit — module stem matches class name (hello.py → Hello).

Default product path used by DirectoryRoutes + mount_surfaces.
"""
from __future__ import annotations

from ux_compose import Component, MorphState, action, control


class Hello(Component):
    id = "hello"
    n = MorphState(0)

    def render(self):
        attrs = control("inc")
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return (
            f'<div id="hello">'
            f"<span>{self.n}</span>"
            f"<button {attr_str}>+1</button>"
            f"</div>"
        )

    @action(caps=())
    def inc(self):
        self.n = int(self.n) + 1
