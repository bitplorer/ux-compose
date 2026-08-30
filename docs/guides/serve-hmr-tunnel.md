# Serve, HMR, and tunnel

> **Diátaxis:** how-to · **Canonical:** `docs/guides/serve-hmr-tunnel.md` · **Layer:** ux-compose
> Architecture: [../internals/hmr.md](../internals/hmr.md) · Ownership: [../FLOW.md](../FLOW.md)
> Product CLI surface: [CLI.md](CLI.md)

## Commands

```bash
uxcompose create-app myapp
cd myapp
uxcompose serve dev                 # origin + ui + channel + CSS watch
uxcompose serve dev --tunnel ngrok
uxcompose serve dev --one-process   # fail-safe: one uvicorn
uxcompose serve prod                # clocks hard off
uxcompose build                     # one-shot minify
uxcompose deploy --provider docker  # raw uvicorn, not serve
uxcompose doctor .
```

`uxcompose serve` with no mode prints help and exits 2.

## What `serve dev` starts

```text
browser → origin (no reload)
            /ux-channel*  → channel worker (no reload)
            everything else → ui worker (reload on *.py)
sibling Tailwind --watch writes output.css
client HEAD-polls /css/output.css and swaps the sheet
```

Full diagram and why: [../internals/hmr.md](../internals/hmr.md).

`--one-process` skips origin/ui/channel and runs one uvicorn. Channel
dies on a `.py` save. Daily path is `serve dev` without the flag.

## Rules

- Do not put a file watcher in `hmr.py`.
- Do not spawn Tailwind inside the worker.
- CSS save must not kill the ui worker.
- Live CSS lives on `serve dev` only.
- `uxcompose build` is one-shot minify — no `--watch`.
- HMR is not `Document.use`. It is `HmrClientMiddleware`.

## Tunnel

```text
uxcompose serve dev --tunnel ngrok|cloudflare
  → health wait → provider → public URL
```

See [CLI.md](CLI.md) for the hard-cut table (`uxcompose` vs `uxdom`).
