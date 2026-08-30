# HMR architecture

> **Diátaxis:** explanation · **Canonical:** `docs/internals/hmr.md` · **Layer:** ux-compose
> How-to: [guides/serve-hmr-tunnel.md](../guides/serve-hmr-tunnel.md)
> Ownership: [FLOW.md](../FLOW.md)

This is the source of truth for how `uxcompose serve dev` live-reloads.
It is **not** Next.js Fast Refresh. A page unit is a Python class. A
`.py` save starts a new ui worker. That is live reload, not a module-graph swap.

## What you type

```bash
uxcompose create-app myapp
cd myapp
uxcompose serve dev                 # default: three processes
uxcompose serve dev --one-process   # fail-safe: one uvicorn
uxcompose serve prod                # clocks off, one process
uxcompose build                     # one-shot minify
uxcompose deploy --provider docker  # raw uvicorn, not serve
```

`uxcompose serve` with no mode prints help and exits 2.

## Three processes (default `serve dev`)

One browser URL. Three OS processes. Names match what each process owns.

```text
browser  ──▶  origin :8080          serve_dev.origin_asgi
                 │                    no reload
                 ├─ /ux-channel*  ─▶  channel worker   app:asgi
                 │                    no reload
                 └─ everything else ▶ ui worker        hmr:asgi_factory
                                      reload on *.py
```

| Process | Code | Owns | Reloads? |
|---------|------|------|----------|
| **origin** | `serve_dev.origin_asgi` | the URL the browser hits; forwards HTTP + WebSocket | no |
| **ui** | `hmr:asgi_factory` wrapping `app:asgi` | routes, Document HTML, `/css`, HMR WS `/__uxcompose/hmr` | yes, `*.py` only |
| **channel** | `app:asgi` | `/ux-channel*` (Intent, morph, session) | no |

`worker_for(path)` is the only router:

- path starts with `/ux-channel` → channel
- everything else, including `/css/output.css` and `/__uxcompose/hmr` → ui

Env the origin reads: `UXCOMPOSE_UI_URL`, `UXCOMPOSE_CHANNEL_URL`.
Do not set them by hand. `serve_dev.run` binds a held loopback socket
(`listen_loopback`) and passes uvicorn `--fd` so there is no
probe-and-close port race.

A sibling Tailwind `--watch` writes `assets/.../output.css`. That is a
compiler next to the three servers, not a fourth server.

## Three clocks

Do not collapse these into one watcher or one flag.

| Clock | Owner | What happens |
|-------|-------|----------------|
| Process reload | ui worker, uvicorn `--reload` + `reload_includes=["*.py"]` | new ui process, cold import, new page class |
| Browser live-reload | `hmr.py` WebSocket `/__uxcompose/hmr` | ui death → client waits for GET 200 → `location.reload()` |
| CSS | `cli.py` sibling Tailwind `--watch` + client HEAD `/css/output.css` | stylesheet swap. No process dies |

`hmr.py` does not watch files and does not spawn Tailwind.
HTML insert is `HmrClientMiddleware`, not `Document.use`.
`assets.py` `_StaticDirASGI` answers HEAD and emits
`ETag(mtime_ns-size)` + `Last-Modified` so the poll sees a same-second rewrite.

CSS writes are excluded from the ui reloader (`*.css`, `assets/*`).
Install `watchfiles` or uvicorn falls back to StatReload and may
ignore those excludes.

## Why channel is a separate process

A `.py` save must reload the page class. uvicorn reload kills the
process that imported that class. If Channel lived in that same
process, in-memory session / morph draft dies with it.

Default `serve dev` keeps Channel in its own process. The ui worker
can die. The channel worker does not. Origin keeps forwarding
`/ux-channel*` to the living worker.

This is process isolation, not a durable store. Restart the channel
worker (or the whole `serve dev`) and in-memory Channel state is
gone. Redis / external store is a later product, not this design.

HMR does **not** add Channel attributes. The only HMR marker in HTML
is the script tag `data-uxcompose-hmr`.

## `--one-process`

Default `serve dev` is the three-process stack above.

`--one-process` is the **fail-safe**, not the product path. It starts
**one** uvicorn (`hmr:asgi_factory` + `--reload`). Routes, HMR, and
Channel share that process.

```text
uxcompose serve dev                 # origin + ui + channel
uxcompose serve dev --one-process   # one uvicorn; Channel dies on *.py save
```

Use it when:

- `httpx` / `starlette` / `websockets` are missing and origin cannot proxy
- you are debugging the stack itself and want fewer moving parts
- a platform cannot spawn the worker children

Do **not** use it as the daily command. On a `.py` save the whole
process dies, so Channel RAM dies with it. That is the old model,
kept on purpose so `serve dev` still runs if the split stack cannot.

`serve prod` is also one process, but it is not `--one-process`.
Prod turns every clock off. No reload, no HMR, no CSS watch.

## `serve prod` vs deploy

| Command | Process | Clocks | Use |
|---------|---------|--------|-----|
| `serve dev` | origin + ui + channel | all on | author machine |
| `serve dev --one-process` | one uvicorn | reload + HMR + CSS watch | fail-safe on the author machine |
| `serve prod` | one uvicorn | all off | local prod-like check |
| `deploy` | raw uvicorn | all off | ship. does not call `serve` |

## What a save does

**Python file save**

1. ui reloader sees `*.py`
2. ui worker dies and a new one imports the new class
3. HMR WebSocket drops
4. client waits until origin/ui answers GET 200
5. `location.reload()` — new HTML, new CSS link
6. channel worker is still the same process
7. browser reconnects `/ux-channel` to that same worker

**CSS / className save**

1. Tailwind `--watch` rewrites `output.css`
2. ui reloader ignores `*.css`
3. client HEAD `/css/output.css` sees a new ETag
4. client clones the stylesheet link and swaps it
5. no process dies, no full page reload

**Why two saves used to double-reload**

One `.py` save used to (a) reload uvicorn and (b) rewrite `output.css`,
which uvicorn also watched. The exclude list + CSS clock split those
two events. That is why `--one-process` still sets
`reload_excludes=["*.css", "assets/*"]`.

## Dead names — do not bring back

`devstack`, `glue_factory`, `pages` worker, `public_asgi`, `owner_for`,
`A` / `X` / `Y`, `--no-css-watch`, `--no-hmr`, `--no-reload` as the
way to choose a clock, `build --watch`, `HmrHub`.

## Files

| File | Owns |
|------|------|
| `src/ux_compose/serve_dev.py` | origin, `worker_for`, held sockets, supervisor |
| `src/ux_compose/hmr.py` | client JS, HMR WS, HTML insert |
| `src/ux_compose/cli.py` | `serve dev` / `serve prod`, sibling Tailwind, `--one-process` |
| `src/ux_compose/assets.py` | HEAD + ETag for `/css` |
| `pyproject.toml` extra `serve` | `httpx`, `starlette`, `websockets`, `watchfiles` |
