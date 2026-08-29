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
              ├─ product host     create-app → build() → serve     ← product door
              ├─ library mount    App.mount / mount_surfaces       ← tests / surfaces
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
uxcompose build
uxcompose serve app:asgi
```

`build(document=)` wraps GET with the author Document. Payload type picks
media type (ADR 0002). DirectoryASGI is the no-Starlette **degrade**, not
a peer product.

`App.mount` remains. It is a **library mount** for tests, surfaces, and
agents. Teaching pages call the product path `create-app` → `build()` and
do not present `App.mount` as a second product.

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

`OverlayChrome` (`kit/overlay.py`) is the shared overlay primitive
(stable scrim / panel / dismiss ids, swipe on dismiss not the root,
selectors-only open plan). Widgets adopt it later. Markup of Dialog /
Sheet / ActionSheet is unchanged this cut.

---

## Degrade is visible

Level 1 code stays correct when Channel / Motion / CEK are absent. That
contract is frozen.

Silence was the defect. `ux_compose.degrade.note` records why a higher
level did not attach. `doctor` prints the list. Return values of
`use_channel` / `use_motion` / `use_cek` do not change.

```python
from ux_compose import degrades
app = App.boot("Shop", level=2)   # degrades to L1 if channel is missing
degrades()                        # evidence, not an exception
```

---

## Residuals expire by teaching

These names still exist so 0.1 tests and old snippets do not break.
Doctor flags them in product trees. Do not invent new ones.

| Residual | Prefer |
|----------|--------|
| `from ux_compose.kit import` in an app | `uxcompose add` |
| `host="batteries"` / `DirectoryRouter` | `host="auto"` + Clock A FastAPI |
| `serve="webassets"` as a product name | `serve="dual_copy"` escape hatch |
| `App.mount` taught as the product path | `build()` |
| quantity `MorphState` | `RefState` + `tick()` / `stamp` |
| root `swipe.*` on an overlay card | swipe on dismiss (`OverlayChrome`) |

---

## Frozen laws (do not reopen)

Isolation · Document SSoT · XOR · Cap Law · Ops-as-data · Morph-then-Play ·
cold import · L0–L3 zero-rewrite · Clock A payload-type media selection ·
import-not-copy specialists.

Capability baseline: every name in `0.1.0` `__all__` remains. New names
are additive.
