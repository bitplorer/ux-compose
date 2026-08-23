# System Flow Map (permanent · residual-free)

> **Start here.** This is the only ownership contract.

---

## 0. One screen

```text
ux-dom      RENDER     tree → __render__ / __async_render__ → HTML str | bytes | stream
                       Document shell: control attrs, runtime script tags, CSP stamp
                       pure DirectoryRoutes + RouterHooks (discovery only)
                       pure-dom DX: doctor | lint | build | profile

ux-compose  PRODUCT    create-app · serve · deploy · doctor
            + DELIVERY HTTP bind, host strategy, live units
            + CHANNEL  wire/ only
            + DEV      HMR (/__uxcompose/hmr) · tunnel (ngrok|cloudflare)

ux-behavior units, MorphState, @action (offline)
ux-channel  Intent/Caps behind wire/ only
```

**Author rule:** Render? → ux-dom. Product app lifecycle? → ux-compose only.

---

## 1. Ownership Law

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Tag trees, dunders, Document shell, pure discovery, pure-dom DX | Product lifecycle, HMR process, tunnel |
| **ux-compose** | Composition, delivery, create-app/serve/deploy/doctor, wire/, **HMR + tunnel under serve** | DOM serialize |

---

## 2. Document.use

Allowed: control, runtime, CSP, style. **Not:** HMR process, FastAPIHost, product App.

---

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

## 6. Forbidden

- Dual product paths on uxdom
- HMR as Document.use product API
- Product code importing ux_channel

See `docs/CLI.md`.
