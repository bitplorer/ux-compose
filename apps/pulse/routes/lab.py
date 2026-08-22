"""Page unit: lab.py → Lab — MorphState/RefState, tabs, form, toast patterns."""
from __future__ import annotations

from ux_compose import Component, MorphState, RefState, action, control, notify, update_with


class Lab(Component):
    id = "lab"
    tab = MorphState("counter")
    count = RefState(0)
    stamp = MorphState("idle")
    name = RefState("")
    email = RefState("")
    note = RefState("")
    valid = MorphState("idle")  # idle | ok | err
    toast = RefState("")

    def render(self):
        tabs = []
        for key, label in (("counter", "Counter"), ("form", "Form"), ("toast", "Toast")):
            sel = "true" if self.tab == key else "false"
            attrs = control("lab.set_tab", tab=key)
            a = " ".join(f'{k}="{v}"' for k, v in attrs.items())
            tabs.append(f'<button class="tab" aria-selected="{sel}" {a}>{label}</button>')

        body = ""
        if self.tab == "counter":
            inc = control("lab.inc")
            dec = control("lab.dec")
            reset = control("lab.reset")
            body = f'''
<div class="card stack">
  <h3>RefState magnitude + Morph stamp</h3>
  <p class="kpi">{int(self.count or 0)}</p>
  <p class="subtle">stamp=<span class="mono">{self.stamp}</span> · Channel-safe quantity plane</p>
  <div class="row">
    <button class="btn" {" ".join(f'{k}="{v}"' for k,v in dec.items())}>−</button>
    <button class="btn primary" {" ".join(f'{k}="{v}"' for k,v in inc.items())}>+</button>
    <button class="btn ghost" {" ".join(f'{k}="{v}"' for k,v in reset.items())}>Reset</button>
  </div>
</div>'''
        elif self.tab == "form":
            save = control("lab.save_form")
            body = f'''
<div class="card stack">
  <h3>Validated form</h3>
  <div class="field"><label>Name</label>
    <input name="name" value="{self.name or ""}" data-action="lab.set_name" /></div>
  <div class="field"><label>Email</label>
    <input name="email" value="{self.email or ""}" data-action="lab.set_email" /></div>
  <div class="field"><label>Note</label>
    <textarea name="note" rows="3">{self.note or ""}</textarea></div>
  <div class="row">
    <button class="btn primary" {" ".join(f'{k}="{v}"' for k,v in save.items())}>Save</button>
    <span class="pill {"ok" if self.valid=="ok" else "warn" if self.valid=="err" else ""}">{self.valid}</span>
  </div>
</div>'''
        else:
            show = control("lab.show_toast")
            hide = control("lab.hide_toast")
            toast_html = ""
            if self.toast:
                toast_html = f'<div class="toast" id="toast">{self.toast}</div>'
            body = f'''
<div class="card stack">
  <h3>Toast plane</h3>
  <p class="muted">One-shot messages via notify + local toast state.</p>
  <div class="row">
    <button class="btn primary" {" ".join(f'{k}="{v}"' for k,v in show.items())}>Show toast</button>
    <button class="btn ghost" {" ".join(f'{k}="{v}"' for k,v in hide.items())}>Dismiss</button>
  </div>
</div>
{toast_html}'''

        return f'''
<section id="lab" class="stack" style="padding:var(--space-6) 0">
  <h1 style="font-family:var(--font-display);font-size:var(--text-xl);margin:0">Interactive lab</h1>
  <p class="muted">Tabs · counter · form · toast — same Component, progressive-safe.</p>
  <div class="tabs">{''.join(tabs)}</div>
  {body}
</section>
'''

    @action(caps=())
    def set_tab(self, tab: str = "counter"):
        if tab in ("counter", "form", "toast"):
            self.tab = tab
        return update_with(self)

    @action(caps=())
    def inc(self):
        self.count = int(self.count or 0) + 1
        self.stamp = "a" if self.stamp == "b" else "b"
        return update_with(self)

    @action(caps=())
    def dec(self):
        self.count = max(0, int(self.count or 0) - 1)
        self.stamp = "a" if self.stamp == "b" else "b"
        return update_with(self)

    @action(caps=())
    def reset(self):
        self.count = 0
        self.stamp = "idle"
        return update_with(self, extra_ops=[notify("reset")])

    @action(caps=())
    def set_name(self, name: str = ""):
        self.name = name
        return update_with(self)

    @action(caps=())
    def set_email(self, email: str = ""):
        self.email = email
        return update_with(self)

    @action(caps=())
    def save_form(self, name: str = "", email: str = "", note: str = ""):
        if name:
            self.name = name
        if email:
            self.email = email
        if note:
            self.note = note
        ok = bool(self.name) and ("@" in str(self.email or ""))
        self.valid = "ok" if ok else "err"
        msg = "Saved" if ok else "Name + valid email required"
        return update_with(self, extra_ops=[notify(msg)])

    @action(caps=())
    def show_toast(self):
        self.toast = "Pulse lab · toast plane active"
        return update_with(self, extra_ops=[notify(self.toast)])

    @action(caps=())
    def hide_toast(self):
        self.toast = ""
        return update_with(self)
