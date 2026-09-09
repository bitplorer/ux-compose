# AGENTS.md — ux-compose

Orientation for humans and agents continuing this package.

**First-time:** [START_HERE.md](START_HERE.md). **Map:** [docs/INDEX.md](docs/INDEX.md).

Read [docs/OWNERSHIP.md](docs/OWNERSHIP.md) (ownership SSoT) then [START_HERE.md](START_HERE.md)
then [docs/INDEX.md](docs/INDEX.md). Public names: `src/ux_compose/__init__.py` `__all__`.

**Floor:** Python **≥ 3.14**. Hard-deps are the pinned specialists in
`pyproject.toml` (`[project].dependencies`): ux-dom, ux-channel, ux-behavior,
ux-motion, `cek-host>=0.1.3`, `cek-surface>=0.1.3`. Clone path:
`pip install -e ".[dev]"` / `pip install -e ".[serve]"`. Create-app path:
`pip install -r requirements.txt`. Missing specialists fail loud.

## Layer ownership (hard cut)

The UX stack is a **layered system of specialists**, not a monolith.
Compose is allowed to look like “the product” to authors. It **imports**
specialists and must **not** reimplement them.

| Layer | Owns | Must **not** own |
|-------|------|------------------|
| **ux-dom** | HTML/CSS/JS trees, `Document`, serialize, pure discovery, `uxdom`, package static | Intent, Cap, Result ops, MorphState, motion IR, product CLI, Tailwind compiler, app asset layout |
| **ux-channel** | Intent / Result / Cap / wire / peers / Cap Host (cek-runtime; ≠ HTTP Product host) | HTML trees, CSS |
| **ux-behavior** | Product behavior, Morph/Ref, `@action`, validation | Raw HTML construction, wire codecs |
| **ux-motion** | Presence / transition plans as data (IR v1) | Product behavior, DOM construction |
| **ux-compose** (this repo) | Author composition + product CLI (`uxcompose`: create-app, build, serve, deploy, doctor) + Tailwind compiler + **WebAssets layout** | Re-implementing Document serialize |

Do not invent a sixth product. `ux-app` is retired.

## Author-facing surface (do not invent names)

From `__all__`: `App`, `Component`, `MorphState`, `RefState`, `action`, `bind`,
`control`, `notify`, `update_with`, `morph_play`, `Level`, `doctor`,
`Surface` / `mount_surfaces`, and DOM tags (`div`, `h1`, `button`, …).

There is **no** public `ux.div` / `when` / `forall` / `Page` on this package.
Do not document them. Tags are imported from `ux_compose`.

## What not to invent

- Product CLI on `uxdom` (`create-app`, product `build`, `serve`, `deploy`)
- Tailwind compiler on ux-dom (`ux_compose.tailwind` + `uxcompose build` own it)
- App asset layout / `WebAssets` on ux-dom (`ux_compose.assets` owns it)
- HMR as a `Document.use` product API
- A file watcher, `HmrHub`, or Tailwind `Popen` inside `hmr.py`
- Tailwind `Popen` inside `serve/dev.py` (compiler watch is `tailwind.start_watch`)
- Origin / `worker_for` / `origin_asgi` / `SIGUSR1` inside `cli.py`
- argparse inside `serve/dev.py`
- Folding `author.py` into `algebra.py` (Atelier convenience ≠ composition algebra)
- Folding `surfaces_host.py` into `surfaces.py` (scan ≠ host bind)
- Folding `brand.py` into `kit/overlay.py` (GET brand ≠ OverlayChrome)
- `kit/construct.py` (copied kit files must not import `ux_compose.kit`; helpers stay at package root as `kit_construct.py`)
- A second OWNERSHIP contract body in `docs/internals/`
- Re-adding `routing/adapters/` (product path is `routing.asgi` / `routing.fastapi`)
- Folding `serve/` into `cli.py`
- Claiming `wire/boot.py` is the only Isolation importer (the door is `wire/`)
- Clock flags (`--no-hmr`, `--no-reload`, `--css-watch`). Modes choose clocks.
- Process-reloading the worker because `input.css` changed
- A second Tailwind `--watch` next to serve's sibling (two writers on `output.css`)
- A single-uvicorn fallback next to origin + ui + channel
- Product code importing `ux_channel` outside compose `wire/`
- A copy of Channel codecs, Document serialize, motion IR, **or the StateStore protocol** in this tree
- Dual product paths
- A second HTTP pipeline, FastAPI HTML `default_response_class`, `StreamingRoute`, or HTTP verbs on page units (see Product host below)
- `location.reload()` as the happy path after a `.py` save (morph first)

## Dev clocks under `uxcompose serve`

Do not collapse these. The stale design is an in-process hub + watcher.

| Clock | Owner | Signal |
|-------|-------|--------|
| Process reload | ui worker, uvicorn `--reload` on `*.py` | new ui process, cold import |
| Browser live-reload | `hmr.py` WebSocket `/__uxcompose/hmr` | ui death → GET 200 → morph; `location.reload()` on fail |
| CSS | `tailwind.start_watch` sibling `--watch` + client HEAD `/css/output.css` | stylesheet swap. No process dies. Spawned by `cli.py`. |

`uxcompose serve dev` is origin + ui + channel. Always.
`uxcompose serve prod` is one process, clocks off.
Missing extras fail closed — no single-uvicorn fallback.
HTML insert is `HmrClientMiddleware`, not `Document.use`.
`assets.py` `_StaticDirASGI` must emit `ETag` / `Last-Modified`.
Architecture: [docs/internals/hmr.md](docs/internals/hmr.md).
Decision: [docs/adr/0005-serve-dev-split.md](docs/adr/0005-serve-dev-split.md).
How-to: [docs/guides/serve-hmr-tunnel.md](docs/guides/serve-hmr-tunnel.md).

## CLI spine

```bash
uxcompose create-app myapp --level 1
uxcompose serve dev
uxcompose build
uxcompose deploy --provider docker
uxcompose doctor .
```

`cli.py` is **argv dispatch**. Each verb's runtime is a sibling module.
Do not fold those in — that is how serve-dev became a god file in the
stale design, and how FileStateStore got cloned into compose.

| Verb | Runtime |
|------|---------|
| `create-app` | `scaffold.py` |
| `build` (CSS minify) | `cli_build.py` — **not** `build.py` (`build.py` is App composition: host.open → Channel → DirectoryRoutes) |
| `serve dev` | `serve/dev.py` origin + ui + channel (ADR 0005). No argparse. |
| `serve prod` | uvicorn in `cli.py` (clocks off; no origin) |
| `serve restart-channel` | `serve/restart.py` |
| `deploy` | `deploy.py` |
| `doctor` | `doctor.py` |
| `add` | `kit/copy.py` |
| CSS `--watch` | `tailwind.start_watch` sibling Tailwind `--watch`. `cli.py` spawns it around serve. Not `hmr.py`. Not `serve/dev.py`. |

Do not put `worker_for` / `origin_asgi` / `SIGUSR1` in `cli.py`.
Do not put argparse in `serve/dev.py`.
Do not re-add `routing/adapters/`. Product path is `routing.asgi` /
`routing.fastapi`.

Module map (every concern → one file, including `algebra.py` vs
`author.py`, `brand.py` vs OverlayChrome, `kit_construct.py` at
package root): [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

Pure-dom: `uxdom doctor | lint | profile | add`.
Product CSS: `uxcompose build` (`ux_compose.tailwind` finds / ensures the CLI).

## Tests

```bash
make test314
# or:
PYTHONPATH=src:. python -m pytest tests/ -q
```

See [docs/guides/TESTING.md](docs/guides/TESTING.md). Regression tests under `tests/regression/`
lock the hard-cut (no product CLI dual path).

## Isolation

Cold import never pulls the wire. `App.use_channel(asgi_app=…)` is the live door.
`app.use_motion()` is the motion door. Level 1 code remains correct at L2/L3.

`uxcompose serve dev` session lives with Channel (`ch.draft`). Origin still
sends Document GET to the ui worker. Compose prepares one sqlite path
(`UXCOMPOSE_STATE_STORE`); `Channel.boot` opens Channel's `FileStateStore`.
Do not reimplement that store in this tree. Redis (`REDIS_URL`) is the
product multi-worker path. Do not route HTML GET to channel — that would
drop HMR for route edits.

## Product host (Clock A)

HTTP Product host (Clock A / ADR 0002) ≠ CEK Cap Host (cek-runtime via
`wire/cek`; channel ADR 0009 / 0010).

Read [docs/reference/host.md](docs/reference/host.md) **before** changing
`routing/`, `build.py`, `scaffold.py`, or `wire/boot.py`. Decision:
[docs/adr/0002-product-host.md](docs/adr/0002-product-host.md).

Do not invent a second HTTP pipeline. Payload type picks media type (`dict` →
JSON, generator → stream, tree/`str` → HTML). Do not set FastAPI
`default_response_class`. Do not use `StreamingRoute`. Do not put HTTP verbs
on page units. Do not boot Channel in `App.boot("auto")`. New media types
follow spec §10 (predicate + both hosts + `tests/unit/test_host.py` + the spec
page in the same change). `build()` wraps GET only with the author Document
(`wrap=`). `attach_motion()` returns instances, not classes.
`App.mount` / `attach_page_router` pass the same `wrap=` as `build()`.
`materialize(route_class=)` fails closed. Scaffold does not emit `page()`.
Examples (`examples/live_asgi.py`) use `build()` for Clock A GET — not a
handmade `@app.get` + `HTMLResponse`. `App.mount` is a secondary door.
