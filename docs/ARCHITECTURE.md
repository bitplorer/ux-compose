# Architecture — ux-compose shape

> **Diátaxis:** explanation · **Canonical:** `docs/ARCHITECTURE.md` · **Layer:** ux-compose
> Ownership law stays [FLOW.md](FLOW.md). Host spec stays [reference/host.md](reference/host.md).
> Decision: [adr/0004-clarity-and-residuals.md](adr/0004-clarity-and-residuals.md).
> Map: [INDEX.md](INDEX.md).

This page is the **shape** document. It does not reopen the frozen mental
model (Isolation Law, L0–L3 zero-rewrite, Clock A host, import-not-copy).
It names the doors so a new contributor cannot invent a second one.

---

## One screen

```text
Author  →  ux_compose (this package root)
              │
              ├─ author helpers   act tick field status maybe_*
              ├─ composition      App Component MorphState @action helpers
              ├─ product host     create-app → serve dev → build → serve prod
              ├─ scan step        App.mount  (called by build())   ← tests / surfaces
              ├─ catalog          ux_compose.kit  +  uxcompose add ← one catalog
              └─ wire/            only importer of channel / CEK   ← Isolation door

Specialists (imported, never copied):
  ux-dom        render / Document
  ux-behavior   MorphState / @action / Ops
  ux-channel    Intent / Cap / Result
  ux-motion     presence plans
```

---

## Rings (C4 + hexagonal ports)

| Ring | Lives in | May import | Must not import |
|------|----------|------------|-----------------|
| **0 Author** | `author.py`, `helpers.py`, `component.py`, DOM re-exports | specialists through compose | `ux_channel`, CEK |
| **1 Host** | `app.py`, `build.py`, `routing/`, `scaffold.py`, CLI | ring 0, FastAPI | channel except via `wire/` |
| **2 Catalog** | `kit/` | ring 0 | channel, product `apps/` |
| **3 Wire port** | `wire/` | channel / CEK / motion attach | product trees |

`wire/` is the only outbound port to the live stack. Cold import of
`ux_compose` never opens it.

---

## One author door

Public names are `ux_compose.__all__`.

- `act`, `tick`, `field`, `status`, `maybe_plan`, `maybe_fade`, `maybe_slide`
  live in `ux_compose.author` and are re-exported at the package root.
- `examples/_common.py` re-exports the **same objects**. Examples do not
  grow a private helper world.
- `control` / `bind` stay. `act` is the POST-form helper; it is not a
  replacement for `bind`.

Do not invent `ux.div`, `when`, `forall`, `Page`, or a second helper module.

---

## One product door

```text
uxcompose create-app myapp --level 1
uxcompose serve dev
uxcompose build
uxcompose serve prod
```

`build(document=)` wraps GET with the author Document. Payload type picks
media type (ADR 0002). DirectoryASGI is the no-Starlette **degrade**, not
a peer product.

`serve dev` clocks (origin + ui + channel) are ADR 0005. This page does
not reopen them. Channel stays off the ui reload path.

`build()` calls `App.mount` internally. One implementation, two callers:

| Caller | Why |
|--------|-----|
| `build()` | Product path — host, CSS, HMR, Document wrap. |
| `App.mount(...)` | Tests, surfaces, agents that do not need the host. |

Mount is the **scan step**, not a second product. Deleting it would drop
capability. Teaching pages call `create-app` → `serve dev`.

---

## One catalog rule

| World | Role |
|-------|------|
| `src/ux_compose/kit/` | Catalog source of truth. Ownable, shadcn-style. |
| `uxcompose add <name>` | Copies the widget into the product tree. The copy is yours. |
| `examples/` | Atelier of patterns. Teaching, not a second catalog. |
| `apps/` | Product demos. They own their files after `add`. |

Product code does **not** `from ux_compose.kit import …`.
Tests, the Atelier studio, and agents still may — doctor teaches the
rule rather than deleting the import path.

### OverlayChrome — edge overlays

`OverlayChrome` (`kit/overlay.py`) owns stable scrim / panel / dismiss
ids, dismiss grammar, handle grammar, shipped enter distances, and the
selectors-only open plan. **Dialog, Sheet, and ActionSheet take chrome
from this primitive.** Markup and Tailwind `class_*` stay on the widget.

| Widget | kind | edge | swipe |
|--------|------|------|-------|
| Dialog | `dialog` | center | dismiss: `click swipe.down` |
| Sheet | `sheet` | right | dismiss: `click swipe.right` |
| ActionSheet | `actionsheet` | bottom | handle: `click swipe.down swipe.vertical threshold:48`; cancel: `click swipe.down` |

Shipped enter distances live on the primitive (`EDGE_SLIDE`): right
`x=28`, bottom `y=32`. Swipe lives on dismiss / handle, never the root
(root `swipe.*` swallows row clicks).

Anchored popovers (Dropdown, ContextMenu, Combobox, Select) and the
Command palette are a **different family**. They do not copy OverlayChrome
ids. Command's panel owns `translate-x` in Tailwind; OverlayChrome `rise`
would collide with that transform. Do not force one primitive onto two
interaction families.

---

## Degrade is visible and per-App

Level 1 code stays correct when Channel / Motion / CEK are absent. That
contract is frozen.

Silence was the defect. Each `App` owns a `DegradeLog`. `note()` writes
the active log and dual-writes a process log so `doctor` always has a
process-wide audit. Two Apps in one process do not leak. Return values
of `use_channel` / `use_motion` / `use_cek` do not change.

```python
from ux_compose import App, degrades
app = App.boot("Shop", level=2)   # degrades to L1 if channel is missing
app.degrade_events                # this App
degrades()                        # active log (process-wide when unbound)
```

---

## Leftovers that expire by teaching

These names still exist so 0.1 tests and old snippets do not break.
**That is the design**, not unfinished work. Deleting them is a
capability drop. Doctor flags them in product trees. Do not invent new
ones. A future major version may drop them; this tree teaches.

| Leftover | Prefer |
|----------|--------|
| `from ux_compose.kit import` in an app | `uxcompose add` |
| `host="batteries"` / `use_host("batteries")` / `DirectoryRouter` | `host="auto"` + Clock A FastAPI |
| `serve="webassets"` as a product name | `serve="dual_copy"` escape hatch |
| Teaching `App.mount` as the product path | `serve dev` + `build()` (mount is the scan step) |
| quantity `MorphState` | `RefState` + `tick()` / `stamp` |
| root `swipe.*` on an overlay card | swipe on dismiss (`OverlayChrome`) |

---

## Git operations (not architecture)

Remote `feat/*`, `kit/*`, `docs/*`, `dx/*` branches are git-ops. They
are not a second product and not a hole in this tree. Living lines:

- `main`
- `release/0.1.0`
- `architecture/clarity-one-door-rebased` (this cut, on current main)

An ops pass retires the rest. A composition PR does not mass-delete
them (that would destroy `release/0.1.0` and unmerged kit experiments).

---

## Frozen laws (do not reopen)

Isolation · Document SSoT · XOR · Cap Law · Ops-as-data · Morph-then-Play ·
cold import · L0–L3 zero-rewrite · Clock A payload-type media selection ·
import-not-copy specialists · `serve dev` clocks (ADR 0005).

Capability baseline: every name in `0.1.0` `__all__` remains. New names
are additive.
