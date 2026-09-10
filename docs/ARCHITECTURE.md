# Architecture — ux-compose shape

> **Diátaxis:** explanation · **Canonical:** `docs/ARCHITECTURE.md` · **Layer:** ux-compose
> Ownership law stays [OWNERSHIP.md](OWNERSHIP.md). Host spec stays [reference/host.md](reference/host.md).
> Decision: [adr/0004-clarity-and-residuals.md](adr/0004-clarity-and-residuals.md).
> Map: [INDEX.md](INDEX.md).

This page is the **shape** document. It does not reopen the frozen mental
model (Isolation Law, L0–L3 zero-rewrite, Clock A host, import-not-copy).
It names the doors so a new contributor cannot invent a second one.

---

## One screen

```text
Author  →  ux_compose (this package root)
              │
              ├─ author helpers   act mark_dirty field status optional_*
              ├─ composition      App Component MorphState @action helpers
              ├─ product host     create-app → serve dev → build → serve prod
              ├─ scan step        App.mount  (called by build())
              ├─ catalog          ux_compose.kit  +  uxcompose add
              └─ wire/            only importer of channel / CEK
```

---

## One product door

```text
uxcompose create-app myapp --level 1
uxcompose serve dev
uxcompose build
uxcompose serve prod
```

`serve dev` clocks stay ADR 0005. Channel stays off the ui reload path.
`build()` calls `App.mount` internally. Mount is the scan step, not a
second product.

---

## Concern → file (lock)

This table is the module map. Do **not** add `docs/MODULE_MAP.md`.
`docs/INDEX.md` stays the audience map; this page owns concern→file.

| Concern | Owner file(s) | Must not |
|---------|---------------|----------|
| Isolation door | `wire/boot.py`, `wire/caps.py`, `wire/cek.py` | `ux_channel` import outside `wire/` |
| Cap mint | `wire/caps.py` | empty-token dual attrs |
| Product CLI | `cli.py` | second verb, clock flags |
| Build / CSS | `cli_build.py`, `tailwind.py`, `assets.py` | Tailwind on ux-dom |
| Product host | `routing/host.py`, `routing/fastapi.py`, `routing/asgi.py`, `routing/core.py` | fold FastAPI into DirectoryASGI |
| Composition | `app.py`, `component.py`, `helpers.py` | clone MorphState / Cap |
| Surfaces / scan | `surfaces.py`, `surfaces_host.py`, `build.py` | second HTTP pipeline |
| Doctor | `doctor.py` | leftover scan as kill |
| Kit catalog / copy | `kit/catalog.py`, `kit/copy.py` | overlay in CATALOG |
| Author helpers on copies | `kit_construct.py` (outside `kit/`) | move under `kit/` |
| HMR | `hmr.py` | `Document.use` HMR |
| Channel scripts | `live_client.py` | fold into `hmr.py` |
| Serve-dev clocks | `serve_dev.py`, `cli.py` | `--one-process` |
| Store lifecycle | `serve_state.py` | compose `FileStateStore` class |
| Probe | `dx/probe.py` | junk-drawer growth |
| Scaffold | `scaffold.py` | product CLI on uxdom |
| Chrome / brand | `chrome.py` | GET chrome in `routes/*.py` `render()` |

---

## OverlayChrome — edge overlays

Dialog, Sheet, and ActionSheet take ids, dismiss grammar, and the open
plan from `kit/overlay.py`. Markup and Tailwind stay on the widget.
Swipe lives on dismiss / handle, never the root.

Anchored popovers and Command are a different family. They do not copy
these ids.

---

## Attach notes — missing specialist, visible step-down

`use_channel` / `use_motion` fail loud when the hard-dep is missing
(`ImportError`). Isolation: product never imports `ux_channel`.
`App.boot("auto")` stays L1 (does not boot Channel).

Attach notes still record non-import step-downs. Two Apps in one process
do not leak. This is not a message bus and not part of HMR.

---

## Leftovers that expire by teaching

These strings are not the product path. Doctor flags them in app trees.

| Leftover | Prefer |
|----------|--------|
| `ux_compose.routing.adapters` | `ux_compose.routing.asgi` / `routing.fastapi` |
| `from ux_compose.kit import` in an app | `uxcompose add` |
| `host="batteries"` / `DirectoryRouter` | `host="auto"` |
| Teaching `App.mount` as a "secondary door" | page-unit scan step; product path is `build()` |
| Teaching `App.mount` as the product path | `build()` |
| root `swipe.*` on an overlay card | swipe on dismiss |
| `stunning-root` / nav brand in `render()` | `brand_wrap(document, brand=…)` / `build(wrap=document)` |

Doctor flags these in product trees. Deleting the aliases is a capability drop.

---

## Frozen laws (do not reopen)

Isolation · Document SSoT · XOR · Cap Law · Ops-as-data · Morph-then-Play ·
cold import · L0–L3 zero-rewrite · Clock A · import-not-copy ·
`serve dev` clocks (ADR 0005).
