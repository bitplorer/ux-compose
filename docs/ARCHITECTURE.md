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
              ├─ catalog scan     App.mount  (scan_surfaces / Behavior)
              ├─ HTTP path law    DirectoryRoutes.discover  (called by build())
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
`build()` calls `App.mount` (catalog scan, `bind_pages=False`) then
`DirectoryRoutes.discover` (HTTP path law). Two walkers, one product
door. Mount is not a second product. Do not merge the walks.

---

## Concern → file (lock)

This table is the module map. Do **not** add `docs/MODULE_MAP.md`.
`docs/INDEX.md` stays the audience map; this page owns concern→file.

| Concern | Owner file(s) | Must not |
|---------|---------------|----------|
| Isolation door | `wire/boot.py`, `wire/caps.py`, `wire/cek.py` | `ux_channel` import outside `wire/` |
| Cap mint | `wire/caps.py` | empty-token dual attrs |
| Product CLI | `cli.py` | second verb, clock flags |
| Build / CSS | `cli_build.py`, `tailwind.py`, `assets.py` | Tailwind on ux-dom; Tailwind `Popen` in `cli.py` / `hmr.py`; leftover `start_css_watcher=` |
| Product host | `routing/host.py`, `routing/fastapi.py`, `routing/asgi.py`, `routing/core.py` | fold FastAPI into DirectoryASGI |
| Composition | `app.py`, `component.py`, `helpers.py` | clone MorphState / Cap |
| Surfaces / scan | `surfaces.py`, `surfaces_host.py`, `build.py` | second HTTP pipeline; fold `scan_surfaces` into `DirectoryRoutes.discover` |
| Doctor | `doctor.py` | leftover scan as kill |
| Kit catalog / copy | `kit/catalog.py`, `kit/copy.py` | overlay in CATALOG |
| Author helpers on copies | `kit_construct.py` (outside `kit/`) | move under `kit/` |
| HMR | `hmr.py` | `Document.use` HMR |
| Channel scripts | `live_client.py` | fold into `hmr.py`; synthesized HTML shell for fragments |
| Serve-dev clocks | `serve_dev.py` (body), `cli.py` (argv) | `--one-process`; clock spawn in `cli.py` |
| Store lifecycle | `serve_state.py` | compose `FileStateStore` class |
| Probe | `dx/probe.py` | junk-drawer growth |
| Scaffold | `scaffold.py` | product CLI on uxdom |
| Chrome / brand | `chrome.py` | GET chrome in `routes/*.py` `render()` |
| Tunnel | `tunnel.py` | Document.use tunnel; start before origin health |
| Deploy | `deploy.py` | product CLI on uxdom; upload secrets |
| Channel restart | `serve_restart.py` | clock flag; `--one-process`; fold into `hmr.py` |
| Author helpers | `author.py` | Caps; HTML walk; live in `helpers.py` |
| Progressive levels | `progressive.py` | optional-package unlock ladder |
| Tag re-exports | `dom.py` | Document serialize |
| Attach notes | `attach_notes.py` | message bus |

---

## Folder law

Folders are **import / copy laws**, not drawers. A new folder is a sixth
product unless it encodes a hard cut. Root files that look homeless are
usually library ∩ CLI, or library imports that copies must keep.

| Folder | Law | Must not live here |
|--------|-----|--------------------|
| `wire/` | only `ux_channel` / CEK import | product / kit / helpers |
| `kit/` | ownable catalog. `uxcompose add` rewrites `from ux_compose.kit.X` → `from .X` and copies `X.py` | library helpers, CLI internals |
| `routing/` | Clock A host pair (FastAPI ≠ DirectoryASGI) | compatibility shims |
| `dx/` | slang leftover (one probe file for doctor) | a second DX product |

Do **not** add `cli/`, `helpers/`, `kit/kit_construct.py`, or `docs/MODULE_MAP.md`.

### Why `kit_construct.py` is next to `component.py`

`apply_slots` / `kit_shell` are the host seam (`render(*, shell=, **slots)`).
They are not a widget and not a `Kit` base (`Kit` is dead). Copies must keep:

```python
from ux_compose.kit_construct import apply_slots, kit_shell
```

the same way they keep `from ux_compose.component import Component`.
If this file moved under `kit/`, copy would rewrite the import to
`from .kit_construct import` and drop a fork into every app. That is the
inorganic tree. 56 lines on purpose.

### Why CLI verbs are not a `cli/` package

`uxcompose = ux_compose.cli:main`. `cli.py` is argv dispatch only.
Each verb's **body** is the concern that is also a library:

| Verb | Body | Also imported as |
|------|------|------------------|
| create-app | `scaffold.py` | `create_app()` |
| build | `cli_build.py` | named because `build.py` is `build()` orchestra |
| serve | `serve_dev.py` / `serve_restart.py` / `serve_state.py` | clocks, ADR 0005 (argv in `cli.py`; spawn here) |
| deploy | `deploy.py` | checklist / images |
| doctor | `doctor.py` | `from ux_compose import doctor` |
| add | `kit/copy.py` | ownable copy, not CLI-only |

Folding those under `cli/` would lie: doctor and `build()` are public
algebra. `cli_build.py` is the CSS minify CLI wrap of `tailwind.py`.

### Three helper modules (not one junk package)

| Module | Owns | Not |
|--------|------|-----|
| `helpers.py` | Ops algebra (`bind` / `control` / `update_with`) + fragment walker residual | kit seams, author `act` |
| `author.py` | public `act` / `mark_dirty` / `optional_*` (ADR 0004) | Caps, HTML walk |
| `kit_construct.py` | `apply_slots` / `kit_shell` | catalog stems |

`_fragment_for_target` prefers `ux_dom.response.serialize.extract_by_id`
when importable (ux-dom#20 / tip `2e894cd`; compose#80 C2). The homemade
walker in `helpers.py` is escape if the owner symbol is absent. Serialize
is already library-owned (`to_html_bytes`). `Fragment` is an invisible
tree shell; `parse_html` / `defHTML` are ingest, not extract. String
`render()` / `html=` (CTO FullShellHello) still need a strip —
`dom_tag.get(id=)` does not cover that path. Deleting the escape drops
fragment-law when the owner is missing. Do not give it a forever
`fragment.py` home (agents will grow it). Do not invent Actions on
ux-dom. Do not merge stale encyclopedia plans #73/#76/#77/#80.

---

## OverlayChrome — edge overlays

Dialog, Sheet, and ActionSheet take ids, dismiss grammar, and the open
plan from `kit/overlay.py`. Markup and Tailwind stay on the widget.
Swipe lives on dismiss / handle, never the root.

Anchored popovers and Command are a different family. They do not copy
these ids. `kit/command.py` owns local `{id}-scrim` / `{id}-panel` /
`{id}-dismiss` plus `click keydown.escape`. It must not import
`kit/overlay.py`.

---

## Attach notes — missing specialist, visible step-down

`use_channel` / `use_motion` fail loud when the hard-dep is missing
(`ImportError`). Isolation: product never imports `ux_channel`.
`App.boot("auto")` stays L1 (does not boot Channel).

Attach notes still record non-import step-downs. Two Apps in one process
do not leak. This is not a message bus and not part of HMR.

---

## Leftovers that expire by teaching

These strings are not the product path. Deleting aliases that tests still
lock is a capability drop.

### Doctor leftover tokens (product trees)

`scan_leftover_aliases` / `scan_kit_product_imports` / `scan_render_chrome`
flag these in app trees. Teaching, not kill.

| Leftover | Prefer |
|----------|--------|
| `host="starlette"` | `auto` \| `fastapi` \| `asgi` (fail closed) |
| `ux_compose.routing.adapters` | `ux_compose.routing.asgi` / `routing.fastapi` |
| `from ux_compose.kit import` in an app | `uxcompose add` |
| `host="batteries"` / `DirectoryRouter` / `use_host("batteries")` | `host="auto"` |
| `serve="webassets"` | package-static `serve="dual_copy"` |
| `stunning-root` / nav brand in `render()` | `brand_wrap(document, brand=…)` / `build(wrap=document)` |

### Agent leftovers (do not recreate)

Not scanned as leftover tokens in product trees. Map locks and argv/docs
names. Doctor will not print these from `scan_leftover_aliases`.

| Leftover | Prefer |
|----------|--------|
| `src/ux_compose/cli/` package | `cli.py` dispatch + verb modules |
| `kit/kit_construct.py` | `ux_compose.kit_construct` (library import) |
| `tests/property/` | drop; no property suite in this tree |
| argv `create` | `uxcompose create-app` |
| argv `development` / `production` / `restart_channel` | `dev` / `prod` / `restart-channel` |
| `start_css_watcher=` on `serve_dev.run` | `serve_dev` calls `start_tailwind_watch` |
| `src/ux_compose/serve/` / `services/` packages | `serve_dev.py` + `cli.py` (no fashion folders) |
| Channel `ops/` / `enhance/` as a compose door | Isolation `wire/` only (`ops_to_wire` is wire dicts) |
| homemade `_fragment_for_target` HTML walker in `helpers.py` | prefer `extract_by_id` (ux-dom#20); KEEP walker as escape if absent; serialize is `to_html_bytes`; no `fragment.py` |
| `docs/MODULE_MAP.md` | this table (INDEX remains the audience map) |
| `pip install ux-compose` / PyPI cell | git clone + `pip install -e ".[serve]"` |
| Teaching `App.mount` as a "secondary door" | catalog scan step; product path is `build()` |
| Teaching `App.mount` as the product path | `build()` |
| Teaching `scan_surfaces` as `DirectoryRoutes.discover` | two walkers; `build()` orchestrates both |
| root `swipe.*` on an overlay card | swipe on dismiss |

---

## Frozen laws (do not reopen)

Isolation · Document SSoT · XOR · Cap Law · Ops-as-data · Morph-then-Play ·
cold import · L0–L3 zero-rewrite · Clock A · import-not-copy ·
`serve dev` clocks (ADR 0005).
