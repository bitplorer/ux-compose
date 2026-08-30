# AGENTS.md — ux-compose

Orientation for humans and agents continuing this package.

**First-time:** [START_HERE.md](START_HERE.md). **Map:** [docs/INDEX.md](docs/INDEX.md).

Read [docs/FLOW.md](docs/FLOW.md) (ownership SSoT) then [START_HERE.md](START_HERE.md)
then [docs/INDEX.md](docs/INDEX.md). Public names: `src/ux_compose/__init__.py` `__all__`.

## Layer ownership (hard cut)

The UX stack is a **layered system of specialists**, not a monolith.
Compose is allowed to look like “the product” to authors. It **imports**
specialists and must **not** reimplement them.

| Layer | Owns | Must **not** own |
|-------|------|------------------|
| **ux-dom** | HTML/CSS/JS trees, `Document`, serialize, pure discovery, `uxdom`, package static | Intent, Cap, Result ops, MorphState, motion IR, product CLI, Tailwind compiler, app asset layout |
| **ux-channel** | Intent / Result / Cap / wire / peers / host runtime | HTML trees, CSS |
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
- `--hmr` requiring `--no-reload` (the old XOR). Both clocks default on
- Process-reloading the worker because `input.css` changed
- A second Tailwind `--watch` next to serve's sibling (two writers on `output.css`)
- Product code importing `ux_channel` outside compose `wire/`
- A copy of Channel codecs, Document serialize, or motion IR in this tree
- Dual product paths
- A second HTTP pipeline, FastAPI HTML `default_response_class`, `StreamingRoute`, or HTTP verbs on page units (see Product host below)

## Dev clocks under `uxcompose serve`

Do not collapse these. The stale design is an in-process hub + watcher.

| Clock | Owner | Signal |
|-------|-------|--------|
| Process reload | `cli.py` → uvicorn `--reload` on `*.py` | new worker, cold import |
| Browser live-reload | `hmr.py` WebSocket `/__uxcompose/hmr` | worker death → GET 200 → `location.reload()` |
| CSS | `cli.py` sibling Tailwind `--watch` + client HEAD `/css/output.css` | stylesheet swap. Worker stays alive |

`--no-reload` / `--no-hmr` / `--no-css-watch` turn a clock off. HTML insert
is `HmrClientMiddleware`, not `Document.use`. `assets.py` `_StaticDirASGI`
must emit `ETag` / `Last-Modified` so the HEAD poll has a validator. How-to:
[docs/guides/serve-hmr-tunnel.md](docs/guides/serve-hmr-tunnel.md).

## CLI spine

```bash
uxcompose create-app myapp --level 1
uxcompose build
uxcompose serve app:asgi --port 8080
uxcompose deploy --provider docker
uxcompose doctor .
```

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

## Product host (Clock A)

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
