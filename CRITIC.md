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
| Offline path works without channel | **PASS** | Pure shim + real Behavior; 48 tests |
| Live path only through `wire/` | **PASS** | `wire/boot.py` sole importer of channel/MotionChannel |
| Doctor teaches + fail-closed | **PASS** | IsolationViolation, unlock messages, dual-Document heuristic |
| Elite-love authoring surface | **PASS** | `update_with`, MorphState, @action, control, scene Plan |

## Recommendation

**Ship 0.1.0** under the frozen mental model.
