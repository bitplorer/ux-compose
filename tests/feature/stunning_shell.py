"""Fixture Component that mirrors the broken StunningCek full-shell-in-render pattern.

Live smoking gun (cek-live-demo/stunning — not in this repo):
- routes/hello.py render() returns a FULL shell ``<div id="stunning-root">…brand
  StunningCek…`` while ``update_with`` targets ``#hello``.
- compose ``helpers.update_with`` / ``_render_html`` dumps that full render into
  the morph payload, so brand + kernel_ssot nest on each click.

This fixture is the in-repo stand-in so the fragment-law suite goes RED without
the stunning tree. Do not "fix" this fixture into a fragment — the RED test
depends on it matching the broken author shape.
"""
from __future__ import annotations

from ux_compose import Component, MorphState, action, update_with

from tests.feature.morph import KERNEL_SSOT_ID, SHELL_BRAND, SHELL_ROOT_ID

HELLO_ID = "hello"


def stunning_full_shell_html(n: int) -> str:
    """Full GET shell: brand chrome wrapping the #hello island (broken pattern)."""
    return (
        f'<div id="{SHELL_ROOT_ID}">'
        f'<header class="brand">{SHELL_BRAND}</header>'
        f'<span id="{KERNEL_SSOT_ID}">kernel_ssot</span>'
        f'<div id="{HELLO_ID}"><span class="count">{int(n)}</span></div>'
        f"</div>"
    )


class FullShellHello(Component):
    """Broken stunning-shaped Hello: render() is the outer shell, id is hello."""

    id = HELLO_ID
    n = MorphState(0)

    def render(self):
        return stunning_full_shell_html(int(self.n or 0))

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        return update_with(self)


class FragmentHello(Component):
    """Correct scaffold-shaped Hello: render() is the #hello fragment only."""

    id = HELLO_ID
    n = MorphState(0)

    def render(self):
        n = int(self.n or 0)
        return f'<div id="{HELLO_ID}"><span class="count">{n}</span></div>'

    @action(caps=())
    def inc(self):
        self.n = int(self.n or 0) + 1
        return update_with(self)
