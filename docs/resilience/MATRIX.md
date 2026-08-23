# UX-Stack Resilience Matrix — Phase 1 (ux-compose track)

Canonical taxonomy: ux-dom `docs/resilience/MATRIX.md`.

## Objective

Verify product-lifecycle ownership, delivery boundaries, and residual-free
FLOW law on the compose surface. Additive tests only.

## Repository safety

- Feature branch: `resilience/matrix-phase1`
- Never force-push `main`. Never rewrite history.
- Existing `tests/regression/test_hard_cut_ownership.py` is **KEEP**.
- Long-running soak excluded from Phase 1 gate.

## Phase 1 focus (compose)

| ID | Focus |
|----|--------|
| OWN / REG | Product CLI on compose; hard-cut residual locks |
| ADV | Sanitize / isolation (map `tests/security`) |
| HARD | Doctor laws, cold isolation |

## Phase 1 command subset

```bash
pytest tests/regression tests/security tests/resilience -q
```
