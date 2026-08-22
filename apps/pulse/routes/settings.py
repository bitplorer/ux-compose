"""Page unit: settings.py → Settings — progressive level + doctor surface."""
from __future__ import annotations

from ux_compose import Component, MorphState, action, control, update_with, doctor


class Settings(Component):
    id = "settings"
    refresh_tick = MorphState(0)

    def render(self):
        report = doctor([], fail=False)
        caps = report.capabilities or {}
        rows = "".join(
            f'<li><span class="dot"></span><span class="mono">{k}</span> '
            f'<span class="pill {"ok" if v else ""}">{"on" if v else "off"}</span></li>'
            for k, v in caps.items()
        )
        teaching = "".join(f"<li class='muted'>{t}</li>" for t in (report.teaching or [])[:4])
        attrs = control("settings.refresh")
        a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f'''
<section id="settings" class="stack" style="padding:var(--space-6) 0">
  <div class="row" style="justify-content:space-between">
    <div>
      <h1 style="font-family:var(--font-display);font-size:var(--text-xl);margin:0">Settings & doctor</h1>
      <p class="muted">Progressive capabilities · Isolation · page-unit evidence</p>
    </div>
    <button class="btn" {a}>Refresh · {int(self.refresh_tick or 0)}</button>
  </div>
  <div class="layout">
    <article class="card">
      <h3>Capabilities</h3>
      <p class="subtle">Detected specialists at runtime</p>
      <ul class="feature-list">{rows}</ul>
      <p class="pill">doctor level L{report.level_available} · ok={report.ok}</p>
    </article>
    <article class="card">
      <h3>Teaching</h3>
      <ul class="feature-list">{teaching or "<li class='muted'>Full stack available</li>"}</ul>
    </article>
  </div>
</section>
'''

    @action(caps=())
    def refresh(self):
        self.refresh_tick = int(self.refresh_tick or 0) + 1
        return update_with(self)
