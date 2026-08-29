# Critic pass — ux-compose 0.1.0

Against the mission kill criteria and Composition Laws (mental model frozen).

## Kill criteria

| Criterion | Verdict | Evidence |
|-----------|---------|----------|
| Package root is `ux-compose` | **PASS** | `src/ux_compose/`, pyproject name |
| No client runtime (React/Vue/JSX/TS) | **PASS** | Pure Python surface only |
| Hard invariants never broken | **PASS** | Isolation AST + Cap Law + XOR helpers + Document SSoT |
| Thin composition root (no re-implementation) | **PASS** | Prefer real specialists; pure shims only when absent |
| Progressive L0–L3 zero-rewrite | **PASS** | Same Component class at L1 and L3; tests prove it |
| Offline path works without channel | **PASS** | Pure shim + real Behavior; offline subset green |
| Live path only through `wire/` | **PASS** | `wire/boot.py` + `wire/caps.py` + `wire/cek.py` sole importers of channel/CEK |
| Doctor teaches + fail-closed | **PASS** | IsolationViolation, unlock messages, dual-Document heuristic |
| Elite-love authoring surface | **PASS** | `update_with`, MorphState, @action, control, scene Plan |

## Post-ship increments (this cut)

- Unified Component: `render()` returns ux-dom tag trees; Component does **not** subclass ux-dom Component (shared MRO with tree verbs collides now or later). Tags re-exported from `ux_compose`.
- Live Cap mint path: `App.mint_cap` / `App.submit_intent` — checkout succeeds only with a real Channel Cap
- Channel FastAPI host: `Behavior.attach(asgi)` owns `Channel.boot`; never `attach(Channel)` (include_router)
- Optional CEK door via `wire/cek.py` (`App.use_cek`) — Isolation-safe, degrades if absent
- Product app: `apps/atelier_shop` (cart + confirm modal + Document shell)
- Presence continuity cookbook: `cookbooks/PRESENCE.md`
- GitHub Actions CI matrix (3.12 offline + 3.14 full stack)
- create-app scaffold emits settings.py + document.py + assets/css/input.css + progressive L1–L3 app (`build(document=)`)

## Clarity cut (2026-08-29) — council / critic

| Gate | Verdict | Note |
|------|---------|------|
| Capability baseline | **HOLD** | Every 0.1.0 `__all__` name remains. `App.mount`, `control`, kit widgets, leftover aliases stay. |
| Mental model | **HOLD** | Isolation, L0–L3, Clock A, import-not-copy untouched. |
| One author door | **PASS** | `author.py` + package `__all__`. `_common` is a re-export. |
| One product door | **PASS** | Taught path is `create-app` → `build()` → `serve`. Mount is a library door. |
| One catalog | **PASS** | Kit is source. `uxcompose add` copies. examples/ is Atelier. |
| Degrade visibility | **PASS** | `note()` on attach ImportError. Does not raise. |
| Overlay primitive | **ADDITIVE** | Widgets not rewritten this cut on purpose. |
| ADR numbering | **PASS** | 0004 for clarity. 0003 reserved by 0002. |

### Residual disagreement (do not hide)

1. Dialog / Sheet / ActionSheet still copy-paste overlay ids. Adopting `OverlayChrome` later is the expire path — doing it now would touch widget markup and risk a visual regression.
2. `degrade._EVENTS` is process-global. Fine for 0.1 doctor evidence. Per-App lists are a later increment.
3. `App.mount` still exists and still works. Teaching calls it a library mount. Deleting it would be a capability drop.
4. Thirty-plus feature branches on the remote are operational clutter, not an architecture hole. Do not delete without an explicit ops pass.

### Soft notes (non-kill)

1. **ux-dom requires Python ≥3.14** — documented; L1 offline works on 3.11+.
2. **Doctor dual-Document** when scanning `examples/` may still list multiple educational Document() calls — product packages construct one Document at boot (`apps/atelier_shop`).
3. After `use_channel`, `App.dispatch` is Host-internal (Behavior skips Caps when `_wire` is set). Live Cap verification is `submit_intent` / Channel edge. This is specialist contract, not a compose bug.

## Recommendation

**Ship 0.1.0** under the frozen mental model. Live Cap + Isolation-safe FastAPI attach + one product app now exist. Do not reopen the mental model.

Clarity cut (ADR 0004) is the follow-on that stops confusion from growing. Merge when the architecture tests on `architecture/clarity-one-door` are green.
