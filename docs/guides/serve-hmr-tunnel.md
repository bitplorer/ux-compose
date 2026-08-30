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

serve prod
  browser → one uvicorn (app:asgi)
  no reload, no HMR, no CSS watch
  serves output.css already on disk
```

Daily author path is `serve dev`. Check what the user will see
with `build` then `serve prod`. Ship with `deploy`.

## Rules

- Do not put a file watcher in `hmr.py`.
- Do not spawn Tailwind inside the worker.
- CSS save must not kill the ui worker.
- Live CSS lives on `serve dev` only.
- `uxcompose build` is one-shot minify — no `--watch`.
- HMR is `HmrClientMiddleware`, not `Document.use`.
- Do not add a flag that couples Channel to the ui worker.

## Tunnel

```text
uxcompose serve dev --tunnel ngrok|cloudflare
  → health wait → provider → public URL
```

See [CLI.md](CLI.md) for the hard-cut table (`uxcompose` vs `uxdom`).
