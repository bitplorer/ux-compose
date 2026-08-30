# Serve, HMR, and tunnel

> **Diátaxis:** how-to · **Canonical:** `docs/guides/serve-hmr-tunnel.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

Extracted from [../FLOW.md](../FLOW.md) §§3–5 (Phase 2 mixed-mode split).
Ownership law stays in FLOW. Product CLI surface: [CLI.md](CLI.md).

## 3. Product CLI

```bash
uxcompose create-app myapp
uxcompose serve app:asgi --port 8080
uxcompose serve app:asgi --no-hmr
uxcompose serve app:asgi --css-watch
uxcompose serve app:asgi --tunnel ngrok
uxcompose deploy --provider docker
uxcompose doctor .
```

---

## 4. HMR (dev delivery)

```text
uxcompose serve
  → uvicorn --reload on *.py
  → asgi_factory → attach_hmr on every worker
  → WebSocket /__uxcompose/hmr
  → client: worker death → wait until GET 200 → location.reload()
  → optional --css-watch: sibling Tailwind --watch writes output.css
  → client HEAD-polls /css/output.css → swap stylesheet if the file changes
--reload and --hmr default on. --css-watch defaults off so
`uxcompose build` minify is not overwritten.
```

Do not put a file watcher in `hmr.py`. Do not spawn Tailwind inside the
worker. CSS save must not kill the Python process. Do not run
`uxcompose build --watch` next to serve's sibling — two writers on
`output.css`.

---

## 5. Tunnel

```text
uxcompose serve --tunnel ngrok|cloudflare
  → health wait → provider → public URL
```

---

See [CLI.md](CLI.md) for the hard-cut table (`uxcompose` vs `uxdom`).
