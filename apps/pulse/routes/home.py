"""Page unit: home.py → Home — landing showcase of the locked product path."""
from __future__ import annotations

from ux_compose import Component, MorphState, action, control, notify, update_with


class Home(Component):
    id = "home"
    pulse = MorphState(0)
    greeting = MorphState("Welcome")

    def render(self):
        n = int(self.pulse or 0)
        attrs = control("home.beat")
        attr = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f'''
<section class="hero" id="home">
  <div class="pill ok">page unit · stem match · App.mount</div>
  <h1>{self.greeting} to <em style="color:var(--accent);font-style:normal">Pulse</em></h1>
  <p class="lede">A live showcase of ux-compose: page units, MorphState, offline dispatch,
  Caps, motion, and doctor evidence — one progressive stack.</p>
  <div class="row">
    <button class="btn primary" {attr}>Pulse · {n}</button>
    <a class="btn" href="/shop">Open shop</a>
    <a class="btn ghost" href="/lab">Interactive lab</a>
  </div>
</section>
<section class="grid">
  <article class="card">
    <h3>Path law</h3>
    <p class="muted">URL = filesystem only. Class name never in the path.
    <span class="mono">home.py → /home</span></p>
  </article>
  <article class="card">
    <h3>Page unit</h3>
    <p class="muted">Stem match picks the owner. Ambiguity fails closed.
    Live instances arrive via <span class="mono">RouterHooks.resolve_unit</span>.</p>
  </article>
  <article class="card">
    <h3>Progressive</h3>
    <p class="muted">Write at L1. Unlock channel and motion later — zero rewrite.
    Isolation Law keeps product code offline-capable.</p>
  </article>
</section>
'''

    @action(caps=())
    def beat(self):
        self.pulse = int(self.pulse or 0) + 1
        self.greeting = "Still here" if self.pulse > 3 else "Welcome"
        return update_with(self, extra_ops=[notify(f"pulse={self.pulse}")])
