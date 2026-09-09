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

## Module map (concern → file)

Do not fold these. Do not invent a sibling for a concern that already
has a file. Public author names stay `ux_compose.__all__` — a file in
this table is the **owner**, not a second public surface.

Moving a file into a package (`serve/`, `cli/`, `kit/construct.py`)
without deleting the old path creates a dual door. Do not do that.

| Concern | Module | Not |
|---------|--------|-----|
| argv dispatch | `cli.py` | origin runtime, CSS `Popen` |
| origin + ui + channel | `serve_dev.py` | argparse, CSS `Popen` |
| SIGUSR1 one-shot | `serve_restart.py` | a clock, a sticky flag |
| store lifecycle | `serve_state.py` | a `FileStateStore` class (Channel owns that) |
| CSS minify verb | `cli_build.py` | `build.py` |
| App composition | `build.py` | CLI minify |
| compiler + `--watch` | `tailwind.py` | `hmr.py`, `serve_dev.py` |
| HMR WS + HTML insert | `hmr.py` | file watcher, Tailwind `Popen` |
| tunnel | `tunnel.py` | `cli.py` runtime |
| create-app | `scaffold.py` | |
| doctor | `doctor.py` | Tailwind compiler |
| deploy | `deploy.py` | `serve` |
| composition algebra | `helpers.py` (`bind` / `control` / `notify` / `update_with` / `morph_play`) | author convenience; serialize clone |
| author convenience | `author.py` (`act` / `field` / `status` / `mark_dirty` / `optional_*`) | algebra. `optional_*` names kept — not an optional fork |
| GET brand wrap | `chrome.py` (`brand_wrap`) | OverlayChrome |
| OverlayChrome | `kit/overlay.py` | GET brand |
| kit slot helpers | `kit_construct.py` (package **root**) | `kit/construct.py` — copied kit files must not import `ux_compose.kit` |
| surface scan | `surfaces.py` | host bind |
| page host bind | `surfaces_host.py` | scan |
| Cap URL tags | `live_client.py` | channel-client clone; Document-absent primary |
| tag re-exports | `dom.py` | Document serialize |
| levels 0–3 | `progressive.py` | a second product |
| attach step-down | `attach_notes.py` | a message bus |
| App façade | `app.py` | |
| Unified Component | `component.py` | subclassing ux-dom `Component` |
| WebAssets | `assets.py` | ux-dom layout |
| filesystem → HTTP | `routing/{core,host,asgi,fastapi}.py` | `routing/adapters/` leftover |
| Isolation door | `wire/` (`boot` / `caps` / `cek`) | any other package; `boot.py` is not the sole importer |
| specialist probe | `dx/probe.py` | Tailwind compiler |
| ownable catalog | `kit/` | product import path (`uxcompose add`) |
| leftover shims | `routing/adapters/` | product path |

Name collisions that are **intentional**, not merge candidates:

| Pair | Why two files |
|------|----------------|
| `cli.py` / `serve_dev.py` | argv vs origin runtime (ADR 0005) |
| `cli_build.py` / `build.py` | CSS minify verb vs App composition |
| `helpers.py` / `author.py` | algebra vs Atelier convenience |
| `chrome.py` / `kit/overlay.py` | GET brand wrap vs overlay widget chrome |
| `surfaces.py` / `surfaces_host.py` | scan vs host bind |
| `hmr.py` / `live_client.py` | reload WS vs Cap URL tags |
| `serve_state.py` vs Channel `FileStateStore` | lifecycle vs store class (ADR 0006) |

`optional_*` on `__all__` is a leftover name (specialists are hard-deps).
Expire by teaching (ADR 0004). Do not rename this cut.

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
| `from ux_compose.kit import` in an app | `uxcompose add` |
| `host="batteries"` / `DirectoryRouter` | `host="auto"` |
| `from ux_compose.routing.adapters` | `ux_compose.routing.asgi` / `.fastapi` |
| Teaching `App.mount` as the product path | `build()` |
| root `swipe.*` on an overlay card | swipe on dismiss |
| `stunning-root` / nav brand in `render()` | `brand_wrap(document, brand=…)` / `build(wrap=document)` |

Doctor flags these in product trees. Deleting the aliases is a capability drop.

---

## Frozen laws (do not reopen)

Isolation · Document SSoT · XOR · Cap Law · Ops-as-data · Morph-then-Play ·
cold import · L0–L3 zero-rewrite · Clock A · import-not-copy ·
`serve dev` clocks (ADR 0005).
