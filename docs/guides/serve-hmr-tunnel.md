# Serve, HMR, and tunnel

> **Diátaxis:** how-to · **Canonical:** `docs/guides/serve-hmr-tunnel.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

Extracted from [../FLOW.md](../FLOW.md) §§3–5 (Phase 2 mixed-mode split).
Ownership law stays in FLOW. Product CLI surface: [CLI.md](CLI.md).

## 3. Product CLI

```bash
uxcompose create-app myapp
uxcompose serve dev
uxcompose serve dev --tunnel ngrok
uxcompose serve prod
uxcompose build
uxcompose deploy --provider docker
uxcompose doctor .
```

---

## 4. HMR (dev delivery)

```text
uxcompose serve dev
  → uvicorn --reload on *.py
  → asgi_factory → attach_hmr on every worker
  → WebSocket /__uxcompose/hmr
  → client: worker death → wait until GET 200 → location.reload()
  → sibling Tailwind --watch writes output.css
  → client HEAD-polls /css/output.css → swap stylesheet
uxcompose serve prod
  → clocks hard off; serves output.css already on disk
uxcompose serve          → help, exit 2
```

Do not put a file watcher in `hmr.py`. Do not spawn Tailwind inside the
worker. CSS save must not kill the Python process. Live CSS lives on
`serve dev` only. `uxcompose build` is one-shot minify — no `--watch`.

---

## 5. Tunnel

```text
uxcompose serve dev --tunnel ngrok|cloudflare
  → health wait → provider → public URL
```

---

See [CLI.md](CLI.md) for the hard-cut table (`uxcompose` vs `uxdom`).
