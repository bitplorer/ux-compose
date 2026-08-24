# System Flow Map (permanent · residual-free)

> **Diátaxis:** explanation · **Canonical:** `docs/FLOW.md` · **Layer:** ux-compose  
> Map: [INDEX.md](INDEX.md).

> **Start here.** This is the only ownership contract.

---

## 0. One screen

```text
ux-dom      RENDER     tree → __render__ / __async_render__ → HTML str | bytes | stream
                       Document shell: control attrs, runtime script tags, CSP stamp
                       pure DirectoryRoutes + RouterHooks (discovery only)
                       Tailwind compiler resolution (discover_css_io / resolve_tailwind / argv_with_io)
                       pure-dom DX: doctor | lint | profile | add

ux-compose  PRODUCT    create-app · build · serve · deploy · doctor
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
| **ux-dom** | Tag trees, dunders, Document shell, pure discovery, Tailwind *compiler resolution*, pure-dom DX | Product lifecycle, HMR process, tunnel |
| **ux-compose** | Composition, delivery, create-app/**build**/serve/deploy/doctor, wire/, **HMR + tunnel under serve** | DOM serialize, Tailwind CLI finder |

`uxcompose build` hands off to `ux_dom.cli.tailwind`. Compose never re-implements the resolver. `uxdom build` is Document/static verify for pure-dom `app/main.py` trees — not the product path.

---

## 2. Document.use

Allowed: control, runtime, CSP, style. **Not:** HMR process, FastAPIHost, product App.

create-app emits `document.py` (one Document + `page()`) and `settings.py` (WebAssets). `build(document=)` attaches that Document. Dual-Document in product files is a doctor fail.

---

## 3–5. Product CLI / HMR / tunnel

How-to: [guides/serve-hmr-tunnel.md](guides/serve-hmr-tunnel.md) · [guides/CLI.md](guides/CLI.md) · [guides/TAILWIND.md](guides/TAILWIND.md).

## 6. Forbidden

- Dual product paths on uxdom
- HMR as Document.use product API
- Product code importing ux_channel
- Re-implementing the Tailwind CLI finder in compose

See [guides/CLI.md](guides/CLI.md).
