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
```

---

## One product door

```text
uxcompose create-app myapp --level 1
uxcompose serve dev
uxcompose build
uxcompose serve prod
```

`serve dev` clocks (origin + ui + channel) are ADR 0005. This page does
not reopen them. Channel stays off the ui reload path.

`build()` calls `App.mount` internally. Mount is the scan step, not a
second product.

---

## Attach notes — missing specialist, visible step-down

Level 1 code stays correct when Channel / Motion / CEK are absent.

If `use_channel` cannot import ux-channel, the App does **not** raise.
It stays at L1 and writes one `AttachNote`:

- `door` — which attach (`use_channel`)
- `wanted` — what was asked (`L2`)
- `reason` — why it stepped down
- `level_kept` — what still runs (`1`)

```python
from ux_compose import App, attach_notes
app = App.boot("Shop", level=2)   # stays L1 if channel is missing
app.attach_notes                 # this App
attach_notes()                   # process-wide when no App is bound
```

Two Apps in one process do not leak. `use_channel` / `use_motion` /
`use_cek` still return `self`. Doctor prints the same rows.

This is not a message bus and not part of HMR. File-save still reloads
the ui process only.

---

## Frozen laws (do not reopen)

Isolation · Document SSoT · XOR · Cap Law · Ops-as-data · Morph-then-Play ·
cold import · L0–L3 zero-rewrite · Clock A · import-not-copy ·
`serve dev` clocks (ADR 0005).
