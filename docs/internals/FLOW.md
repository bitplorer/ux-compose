# System Flow Map (explanation slot)

> **Diátaxis:** explanation · **Canonical ownership:** [../FLOW.md](../FLOW.md) · **Layer:** ux-compose  
> Map: [../INDEX.md](../INDEX.md).

Same contract as [../FLOW.md](../FLOW.md). If they disagree, **FLOW.md wins**.

---

## 0. One screen

```text
ux-dom      RENDER     tree → __render__ / __async_render__ → HTML str | bytes | stream
                       Document shell: control attrs, runtime script tags, CSP stamp
                       pure DirectoryRoutes + RouterHooks (discovery only)
                       WebAssets *paths*, className, stylesheet <link>
                       pure-dom DX: doctor | lint | profile | add

ux-compose  PRODUCT    create-app · build · serve · deploy · doctor
            + CSS      Tailwind CLI finder / ensure / minify (ux_compose.tailwind)
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
| **ux-dom** | Tag trees, dunders, Document shell, pure discovery, WebAssets *paths*, className / `<link>`, pure-dom DX | Product lifecycle, HMR process, tunnel, Tailwind CLI finder |
| **ux-compose** | Composition, delivery, create-app/**build**/serve/deploy/doctor, **Tailwind compiler**, wire/, **HMR + tunnel under serve** | DOM serialize |

`uxcompose build` finds and runs the Tailwind CLI (`ux_compose.tailwind`). `uxdom build` is leftover Document/static verify for `app/main.py` trees — it does not download a compiler.

---

## 2. Document.use

Allowed: control, runtime, CSP, style. **Not:** HMR process, FastAPIHost, product App.

create-app emits `document.py` (one Document + `page()`) and `settings.py` (WebAssets). `build(document=)` attaches that Document.

---

## 3–5. Product CLI / HMR / tunnel

How-to: [../guides/serve-hmr-tunnel.md](../guides/serve-hmr-tunnel.md) · [../guides/CLI.md](../guides/CLI.md) · [../guides/TAILWIND.md](../guides/TAILWIND.md).

## 6. Forbidden

- Dual product paths on uxdom
- HMR as Document.use product API
- Product code importing ux_channel
- Tailwind CLI finder / download living on ux-dom

See [../guides/CLI.md](../guides/CLI.md).
