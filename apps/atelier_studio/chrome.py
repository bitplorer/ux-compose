"""Studio chrome — tokens, catalog page, pattern page. Isolation-safe."""
from __future__ import annotations

from typing import Any, Optional

from ux_compose import (
    HAS_DOM,
    a,
    div,
    footer,
    h1,
    h2,
    header,
    input_,
    p,
    raw,
    section,
    span,
    style,
)
from ux_compose.helpers import _serialize_tree

from examples.catalog import GROUPS, PATTERNS


CSS = """
:root {
  color-scheme: light only;
  --bg: #f3efe6;
  --bg-elevated: #faf7f1;
  --surface: #fffdf8;
  --fg: #161513;
  --fg-muted: #6b6560;
  --fg-subtle: #8a837b;
  --border: color-mix(in oklab, var(--fg) 12%, transparent);
  --border-strong: color-mix(in oklab, var(--fg) 22%, transparent);
  --accent: #2f3b38;
  --accent-fg: #f3efe6;
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 20px;
  --radius-xl: 28px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;
  --font-display: "Fraunces", "Iowan Old Style", "Palatino Linotype", serif;
  --font-body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1.0625rem;
  --text-lg: 1.25rem;
  --text-xl: clamp(1.6rem, 1.1rem + 1.6vw, 2.2rem);
  --text-2xl: clamp(2.1rem, 1.3rem + 3vw, 3.4rem);
  --leading-tight: 1.1;
  --leading-snug: 1.25;
  --leading-normal: 1.5;
  --tracking-display: -0.03em;
  --ease-out: cubic-bezier(0.22, 1, 0.36, 1);
}
*, *::before, *::after { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
html, body {
  color-scheme: light only;
  background: #f3efe6;
  color: #161513;
  font-family: var(--font-body);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  min-height: 100dvh;
  -webkit-font-smoothing: antialiased;
}
button:not(:disabled), [role="button"]:not(:disabled) { cursor: pointer; }
button:disabled { opacity: 0.6; cursor: wait; }
a { color: inherit; text-decoration: none; }
h1, h2, h3 { text-wrap: balance; font-family: var(--font-display); letter-spacing: var(--tracking-display); }
p { text-wrap: pretty; }
.wrap { width: min(1120px, calc(100% - 32px)); margin: 0 auto; }
.top {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: var(--space-4); padding: var(--space-5) 0 var(--space-4);
  border-bottom: 1px solid var(--border);
}
.brand { font-family: var(--font-display); font-weight: 550; font-size: 1.3rem; }
.brand span { color: var(--fg-muted); font-weight: 450; margin-left: 0.4rem; font-size: 0.95rem; }
.nav-meta { display: flex; gap: var(--space-3); align-items: center; flex-wrap: wrap; color: var(--fg-subtle); font-size: var(--text-sm); letter-spacing: 0.08em; text-transform: uppercase; }
.nav-meta a { border-bottom: 1px solid var(--border-strong); padding-bottom: 1px; }
.level-chip {
  font-size: var(--text-xs); letter-spacing: 0.12em; text-transform: uppercase;
  border: 1px solid var(--border); border-radius: 999px; padding: 4px 10px;
}
.hero { padding: var(--space-8) 0 var(--space-6); display: grid; gap: var(--space-4); max-width: 42rem; }
.kicker { font-size: var(--text-xs); letter-spacing: 0.18em; text-transform: uppercase; color: var(--fg-subtle); margin: 0; }
.hero h1, .pattern-hero h1 {
  font-weight: 550; font-size: var(--text-2xl); line-height: var(--leading-tight); margin: 0;
}
.lede { margin: 0; color: var(--fg-muted); max-width: 46ch; }
.jump {
  display: flex; flex-wrap: wrap; gap: 8px;
  padding: 12px 0 20px; position: sticky; top: 0; z-index: 5;
  background: color-mix(in oklab, var(--bg) 92%, transparent);
  backdrop-filter: blur(10px);
}
.jump a {
  font-size: var(--text-xs); letter-spacing: 0.08em; text-transform: uppercase;
  border: 1px solid var(--border); border-radius: 999px; padding: 8px 12px;
  min-height: 44px; display: inline-flex; align-items: center;
}
.jump a:hover { border-color: var(--border-strong); }
.filter-row { margin: 0 0 var(--space-6); }
#catalog-filter {
  font: inherit; width: 100%; min-height: 44px; padding: 0 14px;
  border: 1px solid var(--border-strong); border-radius: var(--radius-md);
  background: var(--surface); color: var(--fg);
}
.group { padding-bottom: var(--space-7); scroll-margin-top: 64px; }
.group-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--space-4); }
.group-head h2 { margin: 0; font-size: var(--text-lg); font-weight: 550; }
.grid {
  display: grid; grid-template-columns: 1fr; gap: var(--space-4);
}
@media (min-width: 640px) { .grid { grid-template-columns: 1fr 1fr; } }
@media (min-width: 960px) { .grid.cards { grid-template-columns: 1fr 1fr 1fr; } }
.cat-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-xl); padding: var(--space-5);
  display: grid; gap: var(--space-3); min-height: 168px; color: inherit;
  box-shadow: 0 0 0 1px rgba(22,21,19,0.04), 0 1px 2px -1px rgba(22,21,19,0.06);
  transition: transform 150ms var(--ease-out), box-shadow 150ms var(--ease-out);
}
.cat-card:hover { transform: translateY(-1px); box-shadow: 0 0 0 1px rgba(22,21,19,0.08), 0 8px 24px -12px rgba(22,21,19,0.18); }
.cat-card h2 { margin: 0; font-size: var(--text-lg); font-weight: 550; }
.cat-card p { margin: 0; color: var(--fg-muted); font-size: var(--text-sm); }
.chip-row { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.chip, .law {
  font-size: var(--text-xs); letter-spacing: 0.04em;
  border: 1px solid var(--border); border-radius: 999px; padding: 3px 9px;
  color: var(--fg-muted);
}
.law { letter-spacing: 0.08em; text-transform: uppercase; }
.pattern-hero { padding: var(--space-7) 0 var(--space-5); display: grid; gap: var(--space-3); max-width: 40rem; }
.back { color: var(--fg-subtle); font-size: var(--text-sm); }
.layout {
  display: grid; gap: var(--space-6); padding-bottom: var(--space-8); align-items: start;
}
@media (min-width: 880px) {
  .layout { grid-template-columns: minmax(0, 1fr) 320px; }
}
#stage, .stage { min-width: 0; }
.brief {
  background: var(--bg-elevated); border: 1px solid var(--border);
  border-radius: var(--radius-xl); padding: var(--space-5); display: grid; gap: var(--space-3);
}
.brief h2 { margin: 0; font-size: var(--text-lg); font-weight: 550; }
.brief p, .brief li { margin: 0; color: var(--fg-muted); font-size: var(--text-sm); }
.brief .file { font-variant-numeric: tabular-nums; color: var(--fg-subtle); }
.widget {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-xl); padding: var(--space-5);
  display: grid; gap: var(--space-4);
  box-shadow: 0 0 0 1px rgba(22,21,19,0.04);
}
.widget-head { display: grid; gap: 4px; }
.widget-title { margin: 0; font-size: var(--text-xl); font-weight: 550; line-height: var(--leading-snug); }
.row-actions, .seg { display: flex; flex-wrap: wrap; gap: var(--space-2); }
.counter-face { display: flex; align-items: baseline; gap: var(--space-4); margin: 0; }
.num { font-variant-numeric: tabular-nums; font-size: var(--text-2xl); font-family: var(--font-display); font-weight: 550; }
.muted { color: var(--fg-muted); font-size: var(--text-sm); }
.error { color: #7a2e24; margin: 0; }
.status { display: block; font-size: var(--text-sm); }
.status-ok { color: var(--accent); }
.sr { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
.field {
  font: inherit; width: 100%; min-height: 44px; padding: 0 12px;
  border: 1px solid var(--border-strong); border-radius: var(--radius-sm);
  background: var(--surface); color: var(--fg);
}
.stack { display: grid; gap: var(--space-3); margin: 0; }
form.inline { margin: 0; display: inline-flex; }
.btn-primary, .btn-secondary, .btn-ghost, .btn-text, .text-btn {
  font: inherit; border-radius: var(--radius-sm); min-height: 44px; padding: 0 var(--space-4);
}
.btn-primary { background: var(--accent); color: var(--accent-fg); border: 1px solid var(--accent); font-weight: 550; }
.btn-primary:hover { filter: brightness(1.08); }
.btn-primary:active { transform: scale(0.98); }
.btn-secondary { background: transparent; color: var(--fg); border: 1px solid var(--border-strong); font-weight: 550; }
.btn-secondary:hover { background: color-mix(in oklab, var(--fg) 4%, transparent); }
.btn-ghost { background: transparent; border: 1px solid var(--border); color: var(--fg-muted); }
.btn-text, .text-btn {
  background: none; border: 0; color: var(--fg-subtle); min-height: 36px; padding: 0 4px;
  text-decoration: underline; text-underline-offset: 3px; font-size: var(--text-sm);
}
.tab-panel { background: var(--bg-elevated); border-radius: var(--radius-md); padding: var(--space-4); }
.acc-item { border-top: 1px solid var(--border); padding: var(--space-3) 0; display: grid; gap: var(--space-2); }
.dropdown-wrap { position: relative; display: grid; gap: var(--space-2); justify-items: start; }
.menu {
  display: grid; gap: 2px; background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: var(--space-2); min-width: 180px;
}
.drawer-panel {
  background: var(--bg-elevated); border-radius: var(--radius-lg); padding: var(--space-4);
  display: grid; gap: var(--space-3);
}
.bag-lines { list-style: none; padding: 0; margin: 0; display: grid; gap: var(--space-3); }
.bag-line {
  display: grid; grid-template-columns: 1fr auto auto; gap: 4px var(--space-3);
  padding-bottom: var(--space-3); border-bottom: 1px solid var(--border); align-items: center;
}
.bag-line-name { font-weight: 550; }
.bag-line.is-on { background: color-mix(in oklab, var(--fg) 4%, transparent); border-radius: var(--radius-sm); padding: 8px; }
.hit-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 6px; }
.hit, .toast { padding: 8px 0; border-bottom: 1px solid var(--border); }
.kanban { display: grid; grid-template-columns: 1fr; gap: var(--space-3); }
@media (min-width: 720px) { .kanban { grid-template-columns: 1fr 1fr 1fr; } }
.kanban-lane { background: var(--bg-elevated); border-radius: var(--radius-md); padding: var(--space-3); }
.kanban-col { list-style: none; padding: 0; margin: 0; display: grid; gap: var(--space-2); }
.card-mini { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm); padding: 10px; display: grid; gap: 6px; }
.card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: var(--radius-xl); padding: var(--space-5);
  display: grid; gap: var(--space-3); min-height: 200px;
}
.card-head { display: flex; justify-content: space-between; gap: var(--space-3); align-items: baseline; }
.card h2 { margin: 0; font-size: var(--text-lg); font-weight: 550; }
.price { font-variant-numeric: tabular-nums; margin: 0; font-weight: 550; }
.card-line { margin: 0; color: var(--fg-muted); font-size: var(--text-sm); }
.card-mark { color: var(--fg); opacity: 0.72; }
.bag {
  background: var(--bg-elevated); border: 1px solid var(--border);
  border-radius: var(--radius-xl); padding: var(--space-5);
}
.bag-head { display: flex; justify-content: space-between; align-items: baseline; margin-bottom: var(--space-4); }
.bag-head h2 { font-family: var(--font-display); font-size: var(--text-lg); margin: 0; font-weight: 550; }
.bag-count {
  font-variant-numeric: tabular-nums; border: 1px solid var(--border-strong);
  border-radius: 999px; min-width: 1.8rem; height: 1.8rem;
  display: inline-grid; place-items: center; font-size: var(--text-sm); font-weight: 550;
}
.bag-empty-title { font-weight: 550; margin: 0 0 var(--space-2); }
.bag-empty-copy { margin: 0; color: var(--fg-muted); font-size: var(--text-sm); }
.bag-foot { display: flex; justify-content: space-between; font-weight: 550; }
.bag-sum { font-variant-numeric: tabular-nums; font-size: var(--text-lg); }
.bag-notice { color: var(--accent); font-size: var(--text-sm); margin: 0 0 var(--space-3); }
.modal[hidden], .modal[data-open="0"] { display: none; }
.modal[data-open="1"] { position: fixed; inset: 0; z-index: 40; display: grid; place-items: end center; }
@media (min-width: 640px) { .modal[data-open="1"] { place-items: center; } }
.modal-scrim { position: absolute; inset: 0; background: color-mix(in oklab, var(--fg) 38%, transparent); }
.modal-panel {
  position: relative; background: var(--surface); color: var(--fg);
  width: min(420px, 100%); border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  padding: var(--space-6); display: grid; gap: var(--space-3);
}
@media (min-width: 640px) { .modal-panel { border-radius: var(--radius-xl); } }
.modal-panel h2 { font-family: var(--font-display); font-size: var(--text-xl); margin: 0; line-height: var(--leading-snug); }
.modal-copy { margin: 0; color: var(--fg-muted); }
.modal-actions { display: grid; gap: var(--space-2); margin-top: var(--space-3); }
.snack {
  display: flex; justify-content: space-between; align-items: center; gap: var(--space-3);
  background: var(--accent); color: var(--accent-fg); border-radius: var(--radius-sm); padding: 10px 14px;
}
.skel { height: 72px; border-radius: var(--radius-md); background: color-mix(in oklab, var(--fg) 8%, transparent); }
.chip.is-on { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }
.dialog { outline: 2px solid var(--border-strong); }
.bottom-nav, .cal-grid, .kpi-grid {
  display: grid; gap: var(--space-2);
}
.bottom-nav { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.cal-grid { grid-template-columns: repeat(5, minmax(0, 1fr)); }
.kpi-grid { grid-template-columns: 1fr 1fr; }
@media (min-width: 720px) { .kpi-grid { grid-template-columns: 1fr 1fr 1fr; } }
.kpi-tile {
  background: var(--bg-elevated); border-radius: var(--radius-md);
  padding: var(--space-3); display: grid; gap: 4px;
}
.bar {
  height: 8px; border-radius: 999px;
  background: color-mix(in oklab, var(--fg) 10%, transparent);
  position: relative; overflow: hidden;
}
.bar::after {
  content: ""; position: absolute; inset: 0 auto 0 0; width: 0;
  background: var(--accent); border-radius: inherit;
}
.bar-empty::after { width: 0%; }
.bar-low::after { width: 25%; }
.bar-mid::after { width: 60%; }
.bar-full::after { width: 100%; }
.crumbs { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.crumb { font-weight: 550; }
.crumb-sep { color: var(--fg-subtle); }
.popover-panel, .palette-panel, .file-drop {
  background: var(--bg-elevated); border: 1px solid var(--border);
  border-radius: var(--radius-md); padding: var(--space-4);
  display: grid; gap: var(--space-3);
}
.otp-face { letter-spacing: 0.35em; }
.shell-rail.is-collapsed .seg { opacity: 0.72; }
.palette-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 4px; }
.palette-row { padding: 8px 0; border-bottom: 1px solid var(--border); display: flex; gap: var(--space-3); align-items: center; }
.foot {
  border-top: 1px solid var(--border); padding: var(--space-5) 0 var(--space-7);
  color: var(--fg-subtle); font-size: var(--text-sm);
  display: flex; justify-content: space-between; gap: var(--space-4); flex-wrap: wrap;
}
.motion-face {
  display: grid; place-items: center; min-height: 96px;
  border-radius: var(--radius-lg); border: 1px solid var(--border);
  background: var(--bg-elevated);
  font-family: var(--font-display); font-size: var(--text-xl); font-weight: 550;
  transform-origin: 50% 80%;
}
.widget[data-pose="air"] .motion-face {
  background: var(--accent); color: var(--accent-fg); border-color: var(--accent);
}
#from-linen, #to-linen {
  min-width: 88px; min-height: 44px; display: inline-grid; place-items: center;
}
.toast-host {
  position: fixed; inset: auto 16px 16px 16px; z-index: 50;
  display: grid; gap: 8px; pointer-events: none;
  width: min(420px, calc(100% - 32px)); margin: 0 auto;
}
.toast-host .snack { pointer-events: auto; }
@media (prefers-reduced-motion: reduce) {
  .cat-card, .btn-primary, .btn-secondary { transition: none !important; }
}
"""

ENHANCE_JS = """
(() => {
  const swap = (html) => {
    const wrap = document.createElement('div');
    wrap.innerHTML = html.trim();
    const nextStage = wrap.querySelector('#stage');
    const nextModal = wrap.querySelector('#confirm-modal');
    const curStage = document.querySelector('#stage');
    const curModal = document.querySelector('#confirm-modal');
    if (nextStage && curStage) curStage.replaceWith(nextStage);
    if (nextModal && curModal) curModal.replaceWith(nextModal);
  };
  const toastHost = () => document.getElementById('ux-toasts');
  const showToast = (message) => {
    if (!message) return;
    const host = toastHost();
    if (!host) return;
    const row = document.createElement('div');
    row.className = 'snack';
    row.setAttribute('role', 'status');
    row.textContent = String(message);
    host.appendChild(row);
    setTimeout(() => { if (row.parentNode) row.parentNode.removeChild(row); }, 2400);
  };
  const applyOps = async (ops) => {
    const list = Array.isArray(ops) ? ops : [];
    const rest = [];
    const motion = [];
    for (const op of list) {
      const name = String((op && op.op) || '');
      if (name.indexOf('transition.') === 0) motion.push(op);
      else rest.push(op);
    }
    for (const op of rest) {
      if (op && (op.op === 'toast' || op.op === 'notify')) showToast(op.message);
    }
    if (window.UxMotion && typeof window.UxMotion.applyOps === 'function') {
      await window.UxMotion.applyOps(rest);
      await window.UxMotion.applyOps(motion);
      return true;
    }
    return false;
  };
  async function submit(form) {
    const btn = form.querySelector('[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      const body = new URLSearchParams(new FormData(form));
      const res = await fetch(form.action, {
        method: 'POST',
        body: body.toString(),
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
          'X-UX-Ops': '1',
        },
      });
      if (!res.ok) throw new Error('act failed');
      const ctype = res.headers.get('content-type') || '';
      if (ctype.indexOf('application/json') >= 0) {
        const data = await res.json();
        const played = await applyOps(data.ops || []);
        if (data.flash) showToast(data.flash);
        if (!played && data.html) swap(data.html);
      } else {
        swap(await res.text());
      }
    } catch (err) {
      form.removeAttribute('data-ux');
      HTMLFormElement.prototype.submit.call(form);
    } finally {
      if (btn) btn.disabled = false;
    }
  }
  document.addEventListener('submit', (e) => {
    const form = e.target;
    if (!(form instanceof HTMLFormElement)) return;
    if (form.getAttribute('data-ux') !== '1') return;
    e.preventDefault();
    submit(form);
  });
  const filter = document.getElementById('catalog-filter');
  if (filter) {
    const apply = () => {
      const q = String(filter.value || '').toLowerCase();
      document.querySelectorAll('.cat-card').forEach((c) => {
        const hit = !q || (c.textContent || '').toLowerCase().includes(q);
        c.style.display = hit ? '' : 'none';
      });
      document.querySelectorAll('.group').forEach((g) => {
        const any = Array.from(g.querySelectorAll('.cat-card')).some((c) => c.style.display !== 'none');
        g.style.display = any ? '' : 'none';
      });
    };
    filter.addEventListener('input', apply);
  }
})();
"""


def html_of(tree: Any) -> str:
    if tree is None:
        return ""
    if isinstance(tree, str):
        return tree
    return _serialize_tree(tree)


def nav(*, level: int, label: str):
    return header(
        a("Atelier", span("of Patterns"), href="/", className="brand"),
        div(
            a("Shop", href="/shop"),
            span(f"L{level} {label}", className="level-chip"),
            className="nav-meta",
        ),
        className="top wrap",
    )


def catalog_page():
    groups = []
    jumps = []
    for name in GROUPS:
        rows = [r for r in PATTERNS if r["group"] == name]
        if not rows:
            continue
        gid = f"g-{name.lower().replace(' ', '-')}"
        jumps.append(a(name, href=f"#{gid}"))
        cards = []
        for row in rows:
            laws = [span(x, className="law") for x in row["laws"][:3]]
            cards.append(
                a(
                    p(row["kicker"], className="kicker"),
                    h2(row["title"]),
                    p(row["summary"]),
                    div(*laws, className="chip-row"),
                    href=f"/p/{row['slug']}",
                    className="cat-card",
                )
            )
        groups.append(
            section(
                div(
                    h2(name),
                    span(str(len(rows)), className="muted"),
                    className="group-head",
                ),
                div(*cards, className="grid cards"),
                className="group",
                id=gid,
            )
        )
    filter_row = []
    if input_ is not None:
        filter_row = [
            div(
                input_(
                    id="catalog-filter",
                    type="search",
                    placeholder="Filter patterns — counter, checkout, otp…",
                    autocomplete="off",
                    aria_label="Filter patterns",
                ),
                className="filter-row",
            )
        ]
    return (
        section(
            p("99% of product UI", className="kicker"),
            h1("Every pattern is a Component."),
            p(
                f"{len(PATTERNS)} full-length cases. One class each. MorphState, "
                "RefState, @action. Tags from render(). Open a card and press it — "
                "the morph lands, then motion plays.",
                className="lede",
            ),
            className="hero",
        ),
        div(*jumps, className="jump"),
        *filter_row,
        *groups,
    )


def pattern_page(row: dict[str, Any], widget: Any):
    laws = [span(x, className="law") for x in row["laws"]]
    brief = div(
        p("The contract", className="kicker"),
        h2(row["title"]),
        p(row["detail"]),
        div(*laws, className="chip-row"),
        p(row["file"], className="file"),
        className="brief",
    )
    stage = div(widget, id="stage", className="stage")
    return (
        section(
            a("← All patterns", href="/", className="back"),
            p(row["group"], className="kicker"),
            h1(row["title"]),
            p(row["summary"], className="lede"),
            className="pattern-hero",
        ),
        div(stage, brief, className="layout"),
    )


def foot():
    return footer(
        span("ux-compose · tags are the return type"),
        span("No React. Caps on the wire. Morph then play."),
        className="foot wrap",
    )


def toast_host():
    return div(id="ux-toasts", className="toast-host", aria_live="polite")
