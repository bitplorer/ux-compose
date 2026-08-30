# Serve, HMR, and tunnel

> **Diátaxis:** how-to · **Canonical:** `docs/guides/serve-hmr-tunnel.md` · **Layer:** ux-compose
> Architecture: [../internals/hmr.md](../internals/hmr.md)
> Decision: [../adr/0005-serve-dev-split.md](../adr/0005-serve-dev-split.md)
> Ownership: [../FLOW.md](../FLOW.md) · CLI: [CLI.md](CLI.md)

## Commands

```bash
uxcompose create-app myapp
cd myapp
uxcompose serve dev                 # origin + ui + channel + CSS watch
uxcompose serve dev --tunnel ngrok
uxcompose serve prod                # clocks off; build first
uxcompose serve restart-channel     # one-shot Channel RAM drop
uxcompose build                     # one-shot minify
uxcompose deploy --provider docker  # raw uvicorn, not serve
uxcompose doctor .
```

`uxcompose serve` with no mode prints help and exits 2.

Need the origin extras once:

```bash
pip install 'ux-compose[serve]'
```

Missing `httpx` / `starlette` / `websockets` → `serve dev` exits 1.
There is no fallback flag.

## What each mode does

```text
serve dev
  browser → origin
              /ux-channel*     → channel (no reload)
              everything else  → ui (reload on *.py)
  sibling Tailwind --watch writes output.css
  client HEAD-polls /css/output.css and swaps the sheet
  .py save → morph page-unit [id]s; location.reload() only on fail

serve prod
  browser → one uvicorn (app:asgi)
  no reload, no HMR, no CSS watch
  serves output.css already on disk

serve restart-channel
  not a clock — one SIGUSR1 to the origin pidfile
  origin respawns only the channel worker on the same fd
  next *.py save still leaves Channel up
  missing / stale pidfile → exit 1, fail closed
```

Daily author path is `serve dev`. Check what the user will see
with `build` then `serve prod`. Ship with `deploy`.

## What a `.py` save does in the browser

```text
*.py save → ui worker dies → new class imported
         → HMR socket drops → wait GET 200
         → fetch this URL
         → morph matching [id] (Idiomorph if present)
         → on fail: location.reload()
```

Morph choice, in order:

1. `window.Idiomorph` exists → morph `document.body`.
2. Else replace live nodes whose `id` is in the new HTML
   (`Hello.id = "hello"` is the usual target).
3. Else hard reload.

Hard reload also runs when the worker never returns 200, the
response is not HTML, or parse throws. A user tab navigation is
not a save — that path does nothing.

CSS save is a different clock: stylesheet swap, no morph, no reload.
Full diagram: [../internals/hmr.md](../internals/hmr.md).

## When Channel RAM is stale

Default: a `.py` save does **not** restart Channel. MorphState stays.

If that RAM is wrong — stuck session, bad morph cache — drop it once:

```bash
uxcompose serve restart-channel
```

It is an action, not a flag. Do not add `--reload-channel` to `serve dev`.
The next save still leaves Channel up. No running `serve dev` in this
directory → exit 1.

## Rules

- Do not put a file watcher in `hmr.py`.
- Do not spawn Tailwind inside the worker.
- CSS save must not kill the ui worker.
- Live CSS lives on `serve dev` only.
- `uxcompose build` is one-shot minify — no `--watch`.
- HMR is `HmrClientMiddleware`, not `Document.use`.
- Do not add a flag that couples Channel to the ui worker.
- Channel RAM drop is `serve restart-channel`, not a sticky clock.
- Do not make `location.reload()` the happy path again.
  Soft morph first; hard reload is the fallback only.

## Tunnel

```text
uxcompose serve dev --tunnel ngrok|cloudflare
  → health wait → provider → public URL
```

See [CLI.md](CLI.md) for the hard-cut table (`uxcompose` vs `uxdom`).
