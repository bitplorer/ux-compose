# HMR architecture

> **Diátaxis:** explanation · **Canonical:** `docs/internals/hmr.md` · **Layer:** ux-compose
> Decision: [../adr/0005-serve-dev-split.md](../adr/0005-serve-dev-split.md)
> How-to: [../guides/serve-hmr-tunnel.md](../guides/serve-hmr-tunnel.md)
> Ownership: [FLOW.md](../FLOW.md)

This is the source of truth for `uxcompose serve`.
It is **not** Next.js Fast Refresh. A page unit is a Python class.
A `.py` save starts a new ui worker. That is live reload, not a
module-graph swap.

## Product surface

```bash
uxcompose serve dev      # origin + ui + channel + CSS watch
uxcompose serve prod     # one process, clocks off
uxcompose build          # one-shot minify
uxcompose deploy         # raw uvicorn — does not call serve
```

`uxcompose serve` with no mode prints help and exits 2.
There is no flag that changes the process shape.

## `serve dev` — three processes

One browser URL. Names match what each process owns.

```text
browser → origin :8080            serve_dev.origin_asgi  (no reload)
            /ux-channel*       → channel worker app:asgi (no reload)
            everything else    → ui worker hmr:asgi_factory (reload *.py)
```

| Process | Code | Owns | Reloads? |
|---------|------|------|----------|
| **origin** | `serve_dev.origin_asgi` | the URL the browser hits; forwards HTTP + WebSocket | no |
| **ui** | `hmr:asgi_factory` wrapping `app:asgi` | routes, Document HTML, `/css`, HMR WS `/__uxcompose/hmr` | yes, `*.py` only |
| **channel** | `app:asgi` | `/ux-channel*` (Intent, morph, session) | no |

`worker_for(path)` is the only router. Env origin reads:
`UXCOMPOSE_UI_URL`, `UXCOMPOSE_CHANNEL_URL`. Do not set them by hand.

`serve_dev.run` binds a held loopback socket (`listen_loopback`) and
passes uvicorn `--fd`. No probe-and-close port race.

A sibling Tailwind `--watch` writes `output.css`. That is a compiler
next to the three servers, not a fourth server.

## `serve prod` — clocks off

One uvicorn. The browser talks to `app:asgi` directly.
No process reload. No HMR WebSocket. No Tailwind `--watch`.
Whatever `output.css` is on disk is what the page gets.

```bash
uxcompose build
uxcompose serve prod
```

Origin is unused. Nothing is dying, so Channel does not need its own
process. Channel still runs — it just shares the one process.

`serve prod` is a local prod-like check. It is not deploy.
`uxcompose deploy` starts raw uvicorn and never calls `serve`.

## Three clocks (`serve dev` only)

| Clock | Owner | What happens |
|-------|-------|----------------|
| Process reload | ui worker, uvicorn `--reload` + `*.py` | new ui process, cold import, new page class |
| Browser live-reload | `hmr.py` WebSocket `/__uxcompose/hmr` | ui death → wait GET 200 → `location.reload()` |
| CSS | `cli.py` sibling Tailwind `--watch` + client HEAD `/css/output.css` | stylesheet swap. No process dies |

`hmr.py` does not watch files and does not spawn Tailwind.
HTML insert is `HmrClientMiddleware`, not `Document.use`.
`assets.py` `_StaticDirASGI` answers HEAD and emits
`ETag(mtime_ns-size)` + `Last-Modified`.

CSS writes are excluded from the ui reloader (`*.css`, `assets/*`).
Install `watchfiles` or uvicorn may ignore those excludes.

## Why Channel is a separate process

A `.py` save must reload the page class. uvicorn reload kills the
process that imported that class. Channel in that process dies too.

`serve dev` keeps Channel in its own process. The ui worker can die.
Origin keeps forwarding `/ux-channel*` to the living worker.

This is process isolation, not a durable store. Restart the channel
worker (or the whole `serve dev`) and in-memory Channel state is gone.

HMR does **not** add Channel attributes. The only HMR marker in HTML
is the script tag `data-uxcompose-hmr`.

## Fail-safe (not a second architecture)

If `httpx`, `starlette`, or `websockets` are missing, `serve dev`
prints `pip install 'ux-compose[serve]'` and exits 1.

It does **not** fall back to one uvicorn with reload.
If a worker dies after bind, origin stops.
Tailwind missing: CSS watch is skipped, the three processes still run.

## What a save does

**Python file save (`serve dev`)**

1. ui reloader sees `*.py`
2. ui worker dies; a new one imports the new class
3. HMR WebSocket drops
4. client waits until origin/ui answers GET 200
5. `location.reload()` — new HTML
6. channel worker is still the same process
7. browser reconnects `/ux-channel` to that worker

**CSS / className save (`serve dev`)**

1. Tailwind `--watch` rewrites `output.css`
2. ui reloader ignores `*.css`
3. client HEAD `/css/output.css` sees a new ETag
4. client swaps the stylesheet
5. no process dies, no full page reload

**Any save (`serve prod`)**

Nothing. Rebuild CSS with `uxcompose build`. Restart the process
yourself if Python changed.

## Dead names — do not bring back

`devstack`, `glue_factory`, `pages` worker, `public_asgi`, `owner_for`,
`A` / `X` / `Y`, `--one-process`, `--no-css-watch`, `--no-hmr`,
`--no-reload` as a clock switch, `build --watch`, `HmrHub`.

## Files

| File | Owns |
|------|------|
| `src/ux_compose/serve_dev.py` | origin, `worker_for`, held sockets, supervisor |
| `src/ux_compose/hmr.py` | client JS, HMR WS, HTML insert |
| `src/ux_compose/cli.py` | `serve dev` / `serve prod`, sibling Tailwind, extras check |
| `src/ux_compose/assets.py` | HEAD + ETag for `/css` |
| `pyproject.toml` extra `serve` | `httpx`, `starlette`, `websockets`, `watchfiles` |
| `docs/adr/0005-serve-dev-split.md` | the decision |
