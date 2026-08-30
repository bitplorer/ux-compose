# HMR architecture

> **Diátaxis:** explanation · **Canonical:** `docs/internals/hmr.md` · **Layer:** ux-compose
> Decision: [../adr/0005-serve-dev-split.md](../adr/0005-serve-dev-split.md)
> How-to: [../guides/serve-hmr-tunnel.md](../guides/serve-hmr-tunnel.md)
> Ownership: [FLOW.md](../FLOW.md)

This is the source of truth for `uxcompose serve`.
It is **not** Next.js Fast Refresh. A page unit is a Python class.
A `.py` save starts a new ui worker. The browser then **morphs**
matching nodes. `location.reload()` is only the fallback.

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
| Browser live-reload | `hmr.py` WebSocket `/__uxcompose/hmr` | ui death → GET 200 → morph page units; `location.reload()` on fail |
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

Channel state surviving a save and the document staying alive are
different facts. Channel survives because it is another process.
The document stays alive because the client morphs instead of calling
`location.reload()`.

## Fail-safe (not a second architecture)

If `httpx`, `starlette`, or `websockets` are missing, `serve dev`
prints `pip install 'ux-compose[serve]'` and exits 1.

It does **not** fall back to one uvicorn with reload.
If a worker dies after bind, origin stops.
Tailwind missing: CSS watch is skipped, the three processes still run.

## What a save does

**Python file save (`serve dev`)**

```text
*.py save
    │
    v
ui reloader sees *.py ── ui worker dies
    │                        new worker cold-imports the page class
    v
HMR WebSocket /__uxcompose/hmr drops
    │
    v
client reconnects, waits until GET location.href is 200
    │
    v
softReload() fetches the same URL (HTML, cache: no-store)
    │
    +── parse / type / HTTP fail ──────────────+
    v                                              │
morphLive(html)                                    v
    │                                   hardReload() = location.reload()
    +─ Idiomorph on window? ─ yes ─ Idiomorph.morph(body, next body)
    │ no
    v
replace live nodes whose [id] exists in the new HTML
    (skip html, body, data-uxcompose-hmr)
    │
    +─ zero ids matched ─────────────────+
    v                                              │
document stays          channel worker untouched   v
scroll / focus outside  /ux-channel stays          hardReload()
the replaced unit stay
```

Client functions in `src/ux_compose/hmr.py`: `softReload`,
`morphLive`, `hardReload`. There is no `reloadPage`.

**CSS / className save (`serve dev`)**

```text
className or input.css save
    │
    v
Tailwind --watch rewrites output.css
    │
    ui reloader ignores *.css / assets/*
    v
client HEAD /css/output.css sees a new ETag
    │
    v
swapStylesheets() — new <link>, old node removed on load
    │
    v
no process dies, no morph, no location.reload()
```

**Any save (`serve prod`)**

Nothing. Rebuild CSS with `uxcompose build`. Restart the process
yourself if Python changed.

## How morph is chosen

`morphLive(html)` in the HMR client, in this order:

1. `DOMParser` the fetched HTML. No `body` → throw → hard reload.
2. Copy `document.title` from the new document if present.
3. If `window.Idiomorph.morph` exists (Channel often loads it),
   morph `document.body` onto the new body. That is the full-tree path.
4. Otherwise walk every `[id]` in the new body. For each id that
   already exists in the live document, `replaceWith` a clone of the
   new node. Skip `html`, `body`, and `data-uxcompose-hmr`.
   This is the page-unit path — `Hello.id = "hello"` is the target.
5. If step 4 matched zero ids → throw `hmr-no-target` → hard reload.

HMR does not import Channel. Idiomorph is used only when the page
already put it on `window`. Level 1 apps without Channel still morph
by id.

## When hard reload runs

`hardReload()` is `location.reload()`. It runs only when soft reload
cannot apply a coherent patch:

| Trigger | Why |
|---------|-----|
| Health GET never reaches 200 (80 tries) | worker did not come back |
| Soft fetch is not `ok` | `hmr-http` |
| Response is not `text/html` | `hmr-type` |
| Parse yields no `body` | `hmr-parse` |
| No `[id]` targets and no Idiomorph | `hmr-no-target` |
| Idiomorph throws | catch → hard reload |

A user navigation closes the HMR socket with code `1000`.
That path does not morph and does not reload.

## Dead names — do not bring back

`devstack`, `glue_factory`, `pages` worker, `public_asgi`, `owner_for`,
`A` / `X` / `Y`, `--one-process`, `--no-css-watch`, `--no-hmr`,
`--no-reload` as a clock switch, `build --watch`, `HmrHub`, `reloadPage`.

## Files

| File | Owns |
|------|------|
| `src/ux_compose/serve_dev.py` | origin, `worker_for`, held sockets, supervisor |
| `src/ux_compose/hmr.py` | client JS (`softReload` / `morphLive` / `hardReload`), HMR WS, HTML insert |
| `src/ux_compose/cli.py` | `serve dev` / `serve prod`, sibling Tailwind, extras check |
| `src/ux_compose/assets.py` | HEAD + ETag for `/css` |
| `pyproject.toml` extra `serve` | `httpx`, `starlette`, `websockets`, `watchfiles` |
| `docs/adr/0005-serve-dev-split.md` | the decision |
