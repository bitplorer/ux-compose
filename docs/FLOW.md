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
            (+ HMR process co-located with serve when shipped)

ux-behavior units, MorphState, @action (offline)
ux-channel  Intent/Caps behind wire/ only
```

**Author rule:** Render? → ux-dom. Product app lifecycle? → ux-compose only.

---

## 1. Ownership Law (non-negotiable)

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Tag trees, dunders, Document shell (CSP stamp), pure discovery, pure-dom DX | Product scaffold/serve/deploy, host strategy, channel |
| **ux-compose** | Composition root, delivery, **create-app · serve · deploy · doctor**, channel via wire/ | DOM serialize |
| **ux-behavior** | MorphState, `@action` | Wire |
| **ux-channel** | Intent, Caps | Product imports |
| **wire/** | Only door to channel | — |

---

## 2. Document.use

Allowed: control, runtime tags, CSP stamp, style.
**Not:** HMR process, FastAPIHost, product App.

---

## 3. Product CLI (sole path)

```bash
uxcompose create-app myapp
uxcompose serve app:asgi
uxcompose deploy --provider docker
uxcompose doctor .
```

No product create-app / serve / deploy on `uxdom`.

---

## 4. Progressive Levels

| Level | Unlock | Door |
|-------|--------|------|
| L0 | Static trees | ux-dom |
| L1 | MorphState + `@action` | App / mount |
| L2 | Live Caps | use_channel → wire/ |
| L3 | Motion | use_motion → wire/ |

---

## 5. Page Mount

```text
App.mount(package_dir, asgi_app=api)
  → live units + pure DirectoryRoutes + delivery on api
  → tree → dunders (DOM ends) → HTTP on api (compose)
```

---

## 6. Channel

```text
App.use_channel(asgi_app=api) → wire/ → Behavior.attach → Channel.boot
Product code never imports ux_channel.
```

---

## 7. Forbidden

- Dual product App / dual create-app / dual serve-deploy
- HMR as Document.use product API
- CSP owned by host package instead of Document
- Product code importing ux_channel

---

See `docs/CLI.md`.
