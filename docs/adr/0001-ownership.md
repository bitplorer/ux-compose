# ADR 0001 — Render vs product lifecycle

> **Diátaxis:** ADR · **Canonical:** `docs/adr/0001-ownership.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

**Status:** accepted  
**Date:** 2026-08-24 (extracted from FLOW.md; law predates this extract)  
**Amended:** 2026-08-24 — product `build` + Tailwind compiler + **app asset layout** (`ux_compose.assets.WebAssets`) live on ux-compose. ux-dom keeps className, `<link>`, and package static. `WebAssets` / `TailwindCommand` on ux-dom fail closed.

## Context

Authors were mixing render (tag trees, Document) with product lifecycle
(`create-app`, `build`, `serve`, `deploy`, HMR, tunnel). After the hard-cut,
CSS minify still looked like an ux-dom product verb (`uxdom build`) gated on
the old `app/main.py` layout, while `uxcompose create-app` emitted `app.py`.

## Decision

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Tag trees, dunders, Document shell, pure discovery, className / `<link>`, package static, pure-dom DX | Product lifecycle, HMR process, tunnel, Tailwind compiler, app asset layout |
| **ux-compose** | Composition, delivery, create-app/**build**/serve/deploy/doctor, **Tailwind compiler**, **WebAssets layout**, wire/, **HMR + tunnel under serve** | DOM serialize |

**Author rule:** Render? → ux-dom. Product app lifecycle? → ux-compose only.

Product path: `uxcompose create-app` → `build` → `serve` → `deploy`.

## Consequences

- `uxdom create-app` / `serve` / `deploy` are not the product path.
- `uxcompose build` is the product CSS command. App folders are `ux_compose.assets.WebAssets`. `from ux_dom import WebAssets` fails closed.
- `uxdom build` remains Document/static verify for pure-dom `app/main.py`
  trees. It does not compile CSS. `TailwindCommand` fails closed.
- HMR is not a `Document.use` product API.
- Product code does not import `ux_channel` (attach via `App.use_channel`).
- Full contract: [../FLOW.md](../FLOW.md).
