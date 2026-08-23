# ADR 0001 — Render vs product lifecycle

> **Diátaxis:** ADR · **Canonical:** `docs/adr/0001-ownership.md` · **Layer:** ux-compose  
> Map: [INDEX.md](../INDEX.md).

**Status:** accepted  
**Date:** 2026-08-24 (extracted from FLOW.md; law predates this extract)

## Context

Authors were mixing render (tag trees, Document) with product lifecycle
(`create-app`, `serve`, `deploy`, HMR, tunnel).

## Decision

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Tag trees, dunders, Document shell, pure discovery, pure-dom DX | Product lifecycle, HMR process, tunnel |
| **ux-compose** | Composition, delivery, create-app/serve/deploy/doctor, wire/, **HMR + tunnel under serve** | DOM serialize |

**Author rule:** Render? → ux-dom. Product app lifecycle? → ux-compose only.

## Consequences

- `uxdom create-app` / `serve` / `deploy` are not the product path.
- HMR is not a `Document.use` product API.
- Product code does not import `ux_channel` (attach via `App.use_channel`).
- Full contract: [../FLOW.md](../FLOW.md).
