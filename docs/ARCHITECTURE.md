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
              ├─ scan step        App.mount  (called by build())
              ├─ catalog          ux_compose.kit  +  uxcompose add
              └─ wire/            only importer of channel / CEK
```

---

## One product door

```text
uxcompose create-app myapp --level 1
uxcompose serve dev
uxcompose build
uxcompose serve prod
```

`serve dev` clocks stay ADR 0005. Channel stays off the ui reload path.
`build()` calls `App.mount` internally. Mount is the scan step, not a
second product.

---

## OverlayChrome — edge overlays

Dialog, Sheet, and ActionSheet take ids, dismiss grammar, and the open
plan from `kit/overlay.py`. Markup and Tailwind stay on the widget.
Swipe lives on dismiss / handle, never the root.

Anchored popovers and Command are a different family. They do not copy
these ids.

---

## Attach notes — missing specialist, visible step-down

If `use_channel` cannot import ux-channel, the App does not raise. It
stays at L1 and writes one `AttachNote` (`door`, `wanted`, `reason`,
`level_kept`).

```python
from ux_compose import App, attach_notes
app = App.boot("Shop", level=2)   # stays L1 if channel is missing
app.attach_notes                 # this App
attach_notes()                   # process-wide when no App is bound
```

Two Apps in one process do not leak. This is not a message bus and not
part of HMR.

---

## Leftovers that expire by teaching

| Leftover | Prefer |
|----------|--------|
| `from ux_compose.kit import` in an app | `uxcompose add` |
| `host="batteries"` / `DirectoryRouter` | `host="auto"` |
| `from ux_compose.degrade import` | `from ux_compose import attach_notes` |
| Teaching `App.mount` as the product path | `build()` |
| root `swipe.*` on an overlay card | swipe on dismiss |

Doctor flags these in product trees. Deleting the aliases is a capability drop.

---

## Frozen laws (do not reopen)

Isolation · Document SSoT · XOR · Cap Law · Ops-as-data · Morph-then-Play ·
cold import · L0–L3 zero-rewrite · Clock A · import-not-copy ·
`serve dev` clocks (ADR 0005).
