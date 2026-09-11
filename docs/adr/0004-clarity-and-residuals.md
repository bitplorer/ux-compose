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
2. **One product door.** `create-app` → `serve dev` → `build` → `serve prod`.
   `App.mount` is the catalog scan (`scan_surfaces` / Behavior registry)
   inside `build()`. HTTP path law is a second walk:
   `DirectoryRoutes.discover`, also called by `build()` after mount
   (`bind_pages=False` so mount does not bind HTTP). Two walkers, one
   product door. Do not merge them. Do not teach this as one filesystem
   implementation.
3. **One catalog.** `ux_compose.kit` is the source. `uxcompose add` copies.
   `examples/` is the Atelier, not a second catalog. Product trees do not
   import the kit.
4. **Leftovers expire by teaching.** Doctor scans kit-imports and leftover
   aliases in product trees and prints guidance. It does not fail-close on
   them. Deleting aliases while 0.1 tests lock them is a capability drop.
   Cut 3 leftovers (not doctor tokens): argv `development` / `production` /
   `restart_channel`; `start_css_watcher=` on `serve_dev.run`; ghost
   `cli/` / `serve/` / `services/` packages. Prefer frozen serve verbs and
   `serve_dev` calling `start_tailwind_watch`. Homemade `helpers.py`
   `_fragment_for_target` walker stays until ux-dom owns extract (not a
   second serialize; no `fragment.py`). See
   [../ARCHITECTURE.md](../ARCHITECTURE.md) **Agent leftovers**.
5. **Attach step-downs are visible and per-App.** Each `App` owns attach notes (`app.attach_notes`).
   `note()` dual-writes a process notebook so doctor has a process-wide audit.
   Two Apps in one process do not leak. `use_channel` / `use_motion` fail loud
   (`ImportError`) when the hard-dep is missing. Attach notes still
   record non-import step-downs.
6. **OverlayChrome owns edge-overlay chrome.** Dialog, Sheet, and
   ActionSheet take ids, dismiss/handle grammar, and the open plan from
   the primitive. Markup and Tailwind stay on the widget. Handle grammar
   (`swipe.vertical threshold:48`) and shipped enter distances (right
   `x=28`, bottom `y=32`) live on the primitive. Anchored popovers and
   the Command palette are a different family — they do not copy these ids.

## Consequences

- Authors import from `ux_compose`. No second helper world.
- Maintainers point every new doc at [../ARCHITECTURE.md](../ARCHITECTURE.md)
  plus [../OWNERSHIP.md](../OWNERSHIP.md). Do not add a third map.
- Overlay widgets cannot drift on ids / swipe / enter distance: the
  primitive is the single source.
- New media-type conflicts still get **ADR 0003**, not a second pipeline
  and not a reuse of this number.
- Remote feature branches stay until an ops pass. This ADR does not
  delete them.
- This cut does not reopen `serve dev` clocks (ADR 0005). Channel stays
  off the ui reload path.

## Non-goals

- Deleting `App.mount`, `control()`, leftover aliases, or kit import
  paths used by tests.
- Rewriting Dialog / Sheet / ActionSheet Tailwind or tree structure.
- Reopening Clock A, Isolation Law, or the `serve dev` split.
- Mass-deleting remote `feat/*` / `kit/*` branches from a composition PR.
- Forcing Dropdown / ContextMenu / Combobox / Select / Command through
  OverlayChrome (wrong interaction family).
