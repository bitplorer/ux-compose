# ADR 0005 — serve dev isolates Channel from ui reload

> **Status:** accepted · **Date:** 2026-08-30 · **Layer:** ux-compose
> Architecture: [../internals/hmr.md](../internals/hmr.md)
> How-to: [../guides/serve-hmr-tunnel.md](../guides/serve-hmr-tunnel.md)

## Decision

`uxcompose serve` has two modes. Modes choose clocks. They do not
choose a second architecture.

| Command | Process shape | Clocks |
|---------|---------------|--------|
| `serve dev` | origin + ui + channel | all on |
| `serve prod` | one uvicorn (`app:asgi`) | all off |
| `deploy` | raw uvicorn | all off. does not call `serve` |

There is no `--one-process`, `--no-hmr`, `--no-reload`, or
`--css-watch`. Missing origin extras fail closed:

```text
pip install 'ux-compose[serve]'
```

The old single-uvicorn-with-reload path is deleted. It was a second
product pretending to be a fail-safe.

## Why this shape

A page unit is a Python class. A `.py` save must start a new ui
worker so the new class is imported. uvicorn reload kills that
process.

If Channel lives in the same process, in-memory session and morph
draft die with the page class. That is the bug this split exists to
stop.

Origin is a reverse proxy, not an app. It cannot replace ui or
channel. It only asks `worker_for(path)`:

- `/ux-channel*` → channel worker (no reload)
- everything else, including `/css` and `/__uxcompose/hmr` → ui worker
  (reload on `*.py` only)

`serve prod` does not reload, so nothing dies, so origin is unused.

## Benefits

- One story for authors: `serve dev` or `serve prod`.
- Channel RAM survives a page-class reload.
- CSS save does not kill the ui worker (`reload_excludes` + HEAD poll).
- No flag a developer can leave on and silently couple Channel to ui.
- Missing extras print an install line instead of quietly degrading.

## Side effects / costs

- `serve dev` needs `httpx`, `starlette`, `websockets` (and
  `watchfiles` so CSS excludes actually work).
- Origin is another hop. Latency is local-loopback, not a product
  concern on the author machine.
- Process isolation is not a durable store. Restart channel (or the
  whole `serve dev`) and in-memory Channel state is gone. Redis is a
  later product.
- Hitting a worker port directly bypasses origin. Workers bind
  `127.0.0.1` only.
- This is live reload, not Next.js Fast Refresh. The page remounts.

## Rejected alternatives

| Alternative | Why not |
|-------------|---------|
| One uvicorn + reload | Channel dies on every `.py` save |
| Origin + one backend | Extra hop, Channel still dies |
| `--one-process` fail-safe | Second architecture. Easy to leave on |
| Clock flags (`--no-hmr`) | Mode soup. Prod exists for clocks off |
| `build --watch` next to serve | Two writers on `output.css` |

## Consequences for the tree

- `src/ux_compose/serve_dev.py` owns origin, `worker_for`, held sockets.
- `src/ux_compose/hmr.py` owns client JS + HTML insert. No watcher.
- `src/ux_compose/cli.py` owns mode + sibling Tailwind + extras check.
- Dead names: `devstack`, `glue_factory`, `pages` worker, `public_asgi`,
  `owner_for`, `A`/`X`/`Y`, `--one-process`, `--no-css-watch`, `--no-hmr`.
