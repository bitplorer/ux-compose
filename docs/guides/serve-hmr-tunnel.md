# Serve, HMR, and tunnel

> **Diátaxis:** how-to · **Canonical:** `docs/guides/serve-hmr-tunnel.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

Extracted from [../FLOW.md](../FLOW.md) §§3–5 (Phase 2 mixed-mode split).
Ownership law stays in FLOW. Product CLI surface: [CLI.md](CLI.md).

## 3. Product CLI

```bash
uxcompose create-app myapp
uxcompose serve app:asgi --port 8080
uxcompose serve app:asgi --no-reload --hmr
uxcompose serve app:asgi --tunnel ngrok
uxcompose deploy --provider docker
uxcompose doctor .
```

---

## 4. HMR (dev delivery)

```text
uxcompose serve --no-reload --hmr
  → attach_hmr(asgi) watches . + routes
  → WebSocket /__uxcompose/hmr → {type: reload}
  → optional client: ux_compose.hmr.client_script_tag()
Process --reload is uvicorn only (separate from browser HMR).
```

---

## 5. Tunnel

```text
uxcompose serve --tunnel ngrok|cloudflare
  → health wait → provider → public URL
```

---

See [CLI.md](CLI.md) for the hard-cut table (`uxcompose` vs `uxdom`).
