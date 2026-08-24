# ADR 0001 — Render vs product lifecycle

> **Diátaxis:** ADR · **Canonical:** `docs/adr/0001-ownership.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

**Status:** accepted  
**Date:** 2026-08-24 (extracted from FLOW.md; law predates this extract)  
**Amended:** 2026-08-24 — product `build` is compose-only; Tailwind *resolver* stays on ux-dom
**Amended:** 2026-08-24 — Tailwind *compiler resolution* moves to ux-compose. ux-dom keeps WebAssets *paths* + className + `<link>`.

## Context

Authors were mixing render (tag trees, Document) with product lifecycle
(`create-app`, `build`, `serve`, `deploy`, HMR, tunnel). After the hard-cut,
CSS minify still looked like an ux-dom product verb (`uxdom build`) gated on
the old `app/main.py` layout, while `uxcompose create-app` emitted `app.py`.

## Decision

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Tag trees, dunders, Document shell, pure discovery, WebAssets *paths*, className / `<link>`, pure-dom DX | Product lifecycle, HMR process, tunnel, Tailwind CLI finder |
| **ux-compose** | Composition, delivery, create-app/**build**/serve/deploy/doctor, **Tailwind compiler resolution** (`ux_compose.tailwind`), wire/, **HMR + tunnel under serve** | DOM serialize |

**Author rule:** Render? → ux-dom. Product app lifecycle? → ux-compose only.

Product path: `uxcompose create-app` → `build` → `serve` → `deploy`.

## Consequences

- `uxdom create-app` / `serve` / `deploy` are not the product path.
- `uxcompose build` is the product CSS command. The Tailwind CLI finder / download / ensure lives in `ux_compose.tailwind`.
- `uxdom build` remains Document/static verify for pure-dom `app/main.py`
  trees. It does not download a compiler. Product apps (`app.py`) are taught
  to use `uxcompose build`.
- HMR is not a `Document.use` product API.
- Product code does not import `ux_channel` (attach via `App.use_channel`).
- Full contract: [../FLOW.md](../FLOW.md).
