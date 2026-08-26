# System Flow Map (ownership contract)

> **Diátaxis:** explanation · **Canonical:** `docs/FLOW.md` · **Layer:** ux-compose  
> Map: [INDEX.md](INDEX.md).

> **Start here.** This is the only ownership contract.

---

## 0. One screen

```text
ux-dom      RENDER     tree → __render__ / __async_render__ → HTML str | bytes | stream
                       Document shell: control attrs, runtime script tags, CSP stamp
                       className, stylesheet <link>
                       package static (/ux-dom/static/…)
                       pure-dom DX: doctor | lint | profile | add

ux-compose  PRODUCT    create-app · build · serve · deploy · doctor
            + ROUTES   DirectoryRoutes + thin adapters (filesystem → HTTP)
            + CSS      Tailwind CLI finder / ensure / minify (ux_compose.tailwind)
            + ASSETS   app folders (ux_compose.assets.WebAssets) · /css mount
            + DELIVERY HTTP bind, host strategy, live units
            + CHANNEL  wire/ only
            + DEV      HMR (/__uxcompose/hmr) · tunnel (ngrok|cloudflare)

ux-behavior units, MorphState, @action (offline)
ux-channel  Intent/Caps behind wire/ only
```

**Author rule:** Render? → ux-dom. Product app lifecycle? → ux-compose only.

Product path::

    uxcompose create-app myapp
    uxcompose build
    uxcompose serve app:asgi
    uxcompose deploy --provider docker

---

## 1. Ownership Law

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Tag trees, dunders, Document shell, className / `<link>`, package static, pure-dom DX | Product lifecycle, DirectoryRoutes, HMR, tunnel, Tailwind compiler, WebAssets, host strategy |
| **ux-compose** | Composition, delivery, create-app/**build**/serve/deploy/doctor, **DirectoryRoutes**, **Tailwind compiler**, **WebAssets**, wire/, **HMR + tunnel under serve** | DOM serialize |

`uxcompose build` finds and runs the Tailwind CLI (`ux_compose.tailwind`). Compose never re-implements Document serialize. ux-dom does not compile CSS.

---

## 2. Document.use

Allowed: control, runtime, CSP, style. **Not:** HMR process, product App, host strategy.

create-app emits `document.py` (one Document + `page()`) and `settings.py` (`ux_compose.WebAssets`). `build(document=)` attaches that Document. Dual-Document in product files is a doctor fail.

---

## 3–5. Product CLI / HMR / tunnel

How-to: [guides/serve-hmr-tunnel.md](guides/serve-hmr-tunnel.md) · [guides/CLI.md](guides/CLI.md) · [guides/TAILWIND.md](guides/TAILWIND.md).

## 6. Forbidden

- Dual product paths on uxdom
- HMR as Document.use product API
- Product code importing ux_channel
- Tailwind compiler living on ux-dom
- App asset layout (`WebAssets`) living on ux-dom
- Product routing / host / HotReload living on ux-dom

See [guides/CLI.md](guides/CLI.md).

---

## 7. Product host (Clock A)

Page GET is one pipeline. Authors never implement it.

```text
host.open  →  App L1  →  Document  →  Channel.attach(asgi)  →  host.bind
                                                          document.mount
                                                          page routes
```

`routing/fastapi.py` owns GET `/hello`:

    resolve_unit → render() → [JSON as-is | document(tree) → HTMLResponse]

Media type is the payload, not Accept: `dict` → JSON, tree/str → HTML.

Locked:

- FastAPI is the product process (`host="auto"|"fastapi"`). DirectoryASGI is the no-Starlette degrade.
- Page units have no HTTP verbs. Path params come from the Request.
- `App.boot("auto")` is Level 1. Channel binds in `build()` after the process exists.
- One path law (`http_path`): `index.py`/`route.py` → `/`, `[param]` → `{param}`.
- Streaming is a return value, not a route class.
- `host="batteries"` (leftover DirectoryRouter) fails closed.

ADR: [adr/0002-product-host.md](adr/0002-product-host.md).

