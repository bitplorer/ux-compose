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
            + DEV      origin + ui + channel · HMR · CSS sibling --watch · tunnel

ux-behavior units, MorphState, @action (offline)
ux-channel  Intent/Caps behind wire/ only
```

**Author rule:** Render? → ux-dom. Product app lifecycle? → ux-compose only.

Product path::

    uxcompose create-app myapp
    uxcompose serve dev
    uxcompose build
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

create-app emits `document.py` (one Document; host wraps GET) and `settings.py` (`ux_compose.WebAssets`). `build(document=)` attaches that Document. Dual-Document in product files is a doctor fail.

---

## 3–5. Product CLI / HMR / tunnel

How-to: [guides/serve-hmr-tunnel.md](guides/serve-hmr-tunnel.md) · [guides/CLI.md](guides/CLI.md) · [guides/TAILWIND.md](guides/TAILWIND.md).
Architecture: [internals/hmr.md](internals/hmr.md) · decision: [adr/0005-serve-dev-split.md](adr/0005-serve-dev-split.md).

`serve dev` is origin + ui + channel. `serve prod` is one process, clocks off.
Three clocks on `serve dev` only: process reload (`*.py`) · browser WS live-reload · sibling Tailwind `--watch` + client HEAD `/css/output.css`. No watcher and no `Popen` in `hmr.py`. CSS save must not kill the worker.

## 6. Forbidden

- Dual product paths on uxdom
- HMR as Document.use product API
- A file watcher, `HmrHub`, or Tailwind `Popen` inside `hmr.py`
- Process-reloading the worker because `input.css` changed
- Clock flags (`--hmr`, `--no-reload`, `--css-watch`) or a single-uvicorn fallback
- Product code importing ux_channel
- Tailwind compiler living on ux-dom
- App asset layout (`WebAssets`) living on ux-dom
- Product routing / host / HotReload living on ux-dom

See [guides/CLI.md](guides/CLI.md).

---

## 7. Product host (Clock A)

Page GET is one pipeline. Authors never implement it. Spec:
[reference/host.md](reference/host.md) · decision: [adr/0002-product-host.md](adr/0002-product-host.md)
· recipes: [guides/HOST.md](guides/HOST.md).

```text
host.open  →  App L1  →  Document  →  Channel.attach(asgi)  →  host.bind
                                                          document.mount
                                                          page routes
```

`routing/fastapi.py` owns GET `/hello`:

    resolve_unit → render() → payload dispatch
      dict            → JSON (FastAPI encodes)
      generator       → StreamingResponse
      tree / str      → apply_html_document(wrap) → HTMLResponse
      Response        → as-is

Author `document=` is the wrap. A synthesized Document is mount-only
(CSP / static on FastAPI). Payload type picks media type, not Accept.
Trees stay buffered (CSP + `Content-Length`). `str` is HTML, never JSON,
never a stream.

Locked (full table in the spec):

- FastAPI is the product process. DirectoryASGI is the no-Starlette degrade.
- Page units have no HTTP verbs. One path law (`http_path`).
- `App.boot("auto")` is Level 1. Channel binds after the process exists.
- `host="batteries"` fails closed. No `StreamingRoute`. No HTML
  `default_response_class`.
