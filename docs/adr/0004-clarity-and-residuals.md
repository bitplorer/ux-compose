# ADR 0004 — Clarity, one door, residuals expire

> **Diátaxis:** ADR · **Layer:** ux-compose
> Shape: [../ARCHITECTURE.md](../ARCHITECTURE.md). Map: [../INDEX.md](../INDEX.md).

**Status:** accepted
**Date:** 2026-08-29
**Does not reopen:** Isolation Law, L0–L3 zero-rewrite, Clock A (ADR 0002),
import-not-copy.

> ADR 0003 is reserved by ADR 0002 for a future media-type conflict. This
> decision is 0004 so that reservation stays intact.

## Context

0.1.0 shipped a working product path and a frozen mental model. After ship,
three widget worlds (`kit/`, `examples/`, `apps/`), two taught HTTP doors
(`build()` and `App.mount`), a shadow helper module (`examples/_common.py`),
copy-pasted overlay chrome, and silent `except ImportError` made the repo
look like it had more products than it does.

Capability must not drop. Leftover aliases must not be deleted while tests
still lock them. Confusion must stop growing.

## Decision

1. **One author door.** Public helpers live in `ux_compose.author` and are
   re-exported from `ux_compose.__all__`. `examples/_common.py` re-exports
   the same objects.
2. **One product door.** `create-app` → `build()` → `serve`. `App.mount`
   stays as a library mount for tests and surfaces.
3. **One catalog.** `ux_compose.kit` is the source. `uxcompose add` copies.
   `examples/` is the Atelier, not a second catalog. Product trees do not
   import the kit.
4. **Residuals expire by teaching.** Doctor scans kit-imports and leftover
   aliases in product trees and prints guidance. It does not fail-close on
   residuals.
5. **Degrade is visible.** `degrade.note` records attach step-downs.
   Attach methods still do not raise when a specialist is absent.
6. **OverlayChrome is additive.** Shared ids + dismiss grammar + open plan.
   Existing widget markup is unchanged this cut.

## Consequences

- Authors import from `ux_compose`. No second helper world.
- Maintainers point every new doc at [../ARCHITECTURE.md](../ARCHITECTURE.md)
  plus [../FLOW.md](../FLOW.md). Do not add a third map.
- Widgets may adopt `OverlayChrome` later without a rewrite of the
  author-facing API.
- New media-type conflicts still get **ADR 0003**, not a second pipeline
  and not a reuse of this number.

## Non-goals

- Deleting `App.mount`, `control()`, leftover aliases, or kit import
  paths used by tests.
- Rewriting Dialog / Sheet / ActionSheet markup in this cut.
- Reopening Clock A or Isolation Law.
