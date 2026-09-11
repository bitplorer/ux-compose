---
title: TELOS honesty after Cut B (plan only — no fashion restyle)
date: 2026-09-11
artifact_contract: ce-unified-plan/v1
artifact_readiness: implementation-ready
product_contract_source: user-ask + TELOS CLAIMED/EXPORTED/IMPLEMENTED/LOCKED + Framework Lock
execution: plan-artifact-only
compose_tip: 855d929767f512517e36ba49cd40ce0cd496b2e6
channel_tip: 985e58aee76ca683774c4d4d58ab30a1d3b6efee
channel_pin: 15cb1ed9dd03dbee8826823a7ab46efd4f215b5c
dom_pin: e8be99a52bfecd6026c200fa1c3dc6a74f87aacb
behavior_pin: 793f120e3b1388925772cd069b070d7918b78baa
motion_pin: 67ff3f0c4912b70b7056f8226a6f226b6fe93f60
---

# TELOS honesty after Cut B

> **This PR ships the plan only.** Do not restyle `cli/` / `serve/` / `services/`.
> Do not rename public verbs. Do not overlay Clean Architecture. Do not invent
> a sixth product. Do not rewrite encyclopedia in this change.
>
> Later implementers: execute **only** E13 / P0 / P1 **DO** rows that pass
> Pattern / Clarity. One concern per PR. Same-commit completeness (code +
> leftover teaching + lock). Prefer small PRs over a #29-style overshoot.

**Tips inventoried**

| Repo | SHA | Role |
|------|-----|------|
| bitplorer/ux-compose | `855d929767f512517e36ba49cd40ce0cd496b2e6` | **base** — Cut B leftover-teach fragment walker (#72) |
| bitplorer/ux-channel | pin `15cb1ed9dd03dbee8826823a7ab46efd4f215b5c` | Compose lock (Cuts 1–2) |
| bitplorer/ux-channel | tip `985e58aee76ca683774c4d4d58ab30a1d3b6efee` | **main** — Cut C empty Content-Type (#33) |
| bitplorer/ux-dom | `e8be99a52bfecd6026c200fa1c3dc6a74f87aacb` | pin **==** main |
| bitplorer/ux-behavior | `793f120e3b1388925772cd069b070d7918b78baa` | pin **==** main |
| bitplorer/ux-motion | `67ff3f0c4912b70b7056f8226a6f226b6fe93f60` | pin **==** main |
| cek-host / cek-surface | `>=0.1.3` | PyPI latest **0.1.3** (evidenced `pip index`) |

Prior honesty cuts already on this tip: compose #69 (Cap door / Redis) · #70 Cut 3 dual doors · #71 Cut 4 encyclopedia · #72 Cut B walker. Channel Cuts 1–2 (#30/#31), Cut A (#32), Cut C (#33).

## Goal Capsule

Inventory CLAIMED / EXPORTED / IMPLEMENTED / LOCKED gaps (E1–E15) on ux-compose
`855d929` plus the specialist tree the lockfiles actually name. Rank
DO / KEEP / DEAD / DO NOT. Kill fashion restyle, public rename-for-cleanliness,
sibling packages, and docs-first encyclopedia.

Stop when: every E-row has a `path:line`; every DO cites Pattern + Clarity;
humans can ship P0/P1 as separate PRs without re-auditing the tree.

## Product Contract

### Requirements

- R1. E1–E15 inventory with CLAIMED / EXPORTED / IMPLEMENTED / LOCKED status.
- R2. Dual doors, shadow exports, rotting locks, fail-open boundaries, stale docs.
- R3. Dep-tree health: pins vs tips, unused deps, CVEs only when evidenced, channel-pin honesty vs `985e58a`.
- R4. Ranked DO / KEEP / DEAD / DO NOT. Each DO cites evidence `path:line`.
- R5. Kill list honored (fashion folders, Clean Architecture, sibling packages, public rename, docs-first).
- R6. Phase 2 is E13 / P0 / P1 DO rows that pass Pattern / Clarity only.

### Constraints (law, not taste)

- Framework Lock. Isolation Law, L0–L3 zero-rewrite, Clock A (ADR 0002), import-not-copy, ADR 0005 clocks.
- A3. One concern → one owner path (`docs/ARCHITECTURE.md` concern table).
- A8. Frozen public names stay (`uxcompose` verbs, `__all__`, serve modes).
- Isolation. Product code imports Channel only through `wire/`.
- Docs after the code cut. This plan file is the exception.
- Same-commit completeness on later PRs: pin / leftover teaching / lock together.

### Out of scope (this artifact and first code cuts)

- PR #67 (`serve/` package, `helpers.py` → `algebra.py`, public `optional_*` rename).
- Deleting Moved stubs (`docs/CLI.md`, `docs/DX.md`, `docs/internals/OWNERSHIP.md`).
- Kit Cut 2 / sixth product / `fragment.py` / `helpers/` package.
- Merging `uxchannel create-app` into `uxcompose create-app`.
- Reopening Cap Host vs Clock A, or Channel empty-CT (already Cut C on channel).
- CVE hunting without a scanner in this tree.

### Pattern / Clarity tests (Phase 2 gate)

A DO row ships only when **both** pass:

| Test | Pass | Fail |
|------|------|------|
| **Pattern** | Matches an existing leftover-teach / fail-closed / pin-lockstep cut (#56, #70, channel Cut C) | New folder, new public name, new product door |
| **Clarity** | Names the leftover; one concern; same-commit lock | Encyclopedia-only, or “while we’re here” |

---

## E1–E15 inventory

Legend: **C** CLAIMED · **X** EXPORTED · **I** IMPLEMENTED · **L** LOCKED.

### E1 — CLAIMED not on root `__all__`

| Surface | C | X | I | L | Verdict |
|---------|---|---|---|---|---------|
| `App.mint_cap` / `use_cek` | README.md:163 | no (root) | `app.py` methods | notes only | **KEEP** — App methods, not author verbs. AGENTS `__all__` list matches `src/ux_compose/__init__.py:93-180` |
| `require_dom` | tested | `dom.py:81-94` only | yes | `test_hard_deps.py:78-83` | **KEEP** — hard-dep no-op |
| `doctor.scan_*` / `IsolationViolation` | doctor module `__all__` | submodule | `doctor.py:12-24` | `test_doctor_laws.py` | **KEEP** — library algebra, not author verbs |

No missing author verb vs AGENTS.md:52-61.

### E2 — EXPORTED not locked per-name

| Surface | Evidence | Verdict |
|---------|----------|---------|
| DOM tags on `__all__` | `__init__.py:131-178`; AGENTS ellipsis at :61 | **KEEP** — `HAS_DOM` + `REQUIRED`/`ADDED`/`HOST` locked (`test_architecture_public_api.py`) |
| `__version__` | `__init__.py:11,179` | **KEEP** — package metadata, not a door |

### E3 — IMPLEMENTED not exported (root)

Doctor scans, Cap mint, `uxcompose add` are CLI / App / submodule. Not a second public namespace. **KEEP**.

### E4 — Dual doors (live, taught)

| Job | Door A | Door B | Evidence | Verdict |
|-----|--------|--------|----------|---------|
| Product assembly | `build()` | `App.mount` catalog scan | `docs/ARCHITECTURE.md:40-42`, `build.py` “Two walkers, one product door”, lock `test_source_locks.py:448-468` | **KEEP** — two walkers, one product door. Do not merge |
| Doctor | `from ux_compose import doctor` | `uxcompose doctor` → `doctor.main` · `App.doctor(fail=False)` | `cli.py:365-368`, `doctor.py:540+`, `app.py` | **KEEP** — argv delegates to library (compose pattern) |
| Import `build` | `ux_compose.build` | package re-export | `__init__.py:26,95` | **KEEP** |
| Kit | `uxcompose add` | `from ux_compose.kit import` | `kit/__init__.py:1-8`; doctor `scan_kit_product_imports` | **KEEP** — leftover-taught |
| `examples/_common.py` | re-exports `ux_compose.author` | ADR 0004 §1 | `examples/_common.py:3-14`; `test_architecture_public_api.py:63-69` | **KEEP** — shadow export on purpose |

### E5 — Shadow exports

| Surface | Evidence | Verdict |
|---------|----------|---------|
| Tags via `ux_compose.dom` | `dom.py:1-12` re-exports ux-dom | **KEEP** — author surface; serialize stays `to_html_bytes` |
| Motion `scene`/`fade`/`rise`/`slide` | `__init__.py:40` from `ux_motion`; `author.py` `__all__` omits them | **KEEP** — package root is the door |
| Kit `__all__` vs CATALOG | overlay / `AuthDecision` extra; catalog 1:1 stems | **KEEP** — Cut B: Kit is fine |

### E6 — Homonyms (teach, do not rename)

`wire/` (Isolation vs channel codecs) · `doctor` (compose / channel / uxdom) · `create-app` (product vs channel demo) · `ops` (compose `ops_to_wire` dicts vs channel `ops/`). **KEEP**. Rejected: rename compose `wire/` (`docs/ARCHITECTURE.md:203` Channel `ops/`/`enhance/` not a compose door).

### E7 — Rotting locks

| Lock | Frozen | Live | Evidence | Verdict |
|------|--------|------|----------|---------|
| **Channel pin** | `15cb1ed9dd03dbee8826823a7ab46efd4f215b5c` | channel main `985e58aee76ca683774c4d4d58ab30a1d3b6efee` | `pyproject.toml:25`, `Makefile:10`, `scaffold.py:267`, `apps/nook/requirements.txt:5`, `test_hard_deps.py:13`; docs AGENTS.md:145, README.md:157, OWNERSHIP.md:80, host.md:226, ADR 0006:52 | **DO P0** |
| **Compose self-pin** | `6d61c9e616652d996e55a36886ccfec218308c30` | HEAD `855d929` (**+67** commits, `gh compare`) | `scaffold.py:271`, `apps/nook/requirements.txt:1`, `test_hard_deps.py:16,45-46`, `tests/integration/test_scaffold_create_app.py:93-94,188-189`, CHANGELOG.md:215 | **DO P1** |
| Fragment walker | KEEP until ux-dom extract @ `e8be99a` | still no extract-by-id | `helpers.py` `_fragment_for_target`; `test_source_locks.py:108-135` | **KEEP** |

Channel pin docs do **not** lie that `15cb1ed` is channel tip; they freeze it as compose’s pin. Honesty gap: pin is two channel cuts behind (`0383bc1` Cut A encyclopedia; `985e58a` Cut C empty CT). Compose has **zero** hits for `985e58a`.

### E8 — Fail-open boundaries

| Site | Evidence | Intent | Verdict |
|------|----------|--------|---------|
| Serve extras missing | `cli.py:188-196` ImportError → fail closed | product | **KEEP** (already fail-closed) |
| Serve argv synonyms | `cli.py:226-232` exit 2 | leftover | **DEAD** doors, **KEEP** teaching |
| argv `create` | `cli.py:32-46` unknown command exit 2; `test_cli_help.py:66-72` | leftover | **KEEP** — already fail-closed; not silent synonym |
| `_live_channel` | `helpers.py:41` ImportError → None | offline | **KEEP** (`test_source_locks.py:28-34`) |
| `wire/boot._bridge` | `boot.py:47-52` `except Exception: pass` | progressive register | **KEEP** residual — needs cap-bridge characterization; not E13 |
| `routing/fastapi._live_instance` | `fastapi.py:60-68` Exception → None → empty HTML | Clock A GET | **KEEP** residual — changing blank GET is product behavior, not leftover teaching |
| Doctor `--no-fail` / leftover scans | `doctor.py` teaching-not-kill | ADR 0004 §4 | **KEEP** |
| Empty specialist extras | `pyproject.toml:36-40` `dom=[]`…`full=[]` | no-op aliases | **KEEP** (`test_hard_deps.py:69-75`) |
| `HAS_DOM = True` | `dom.py:78` | hard-dep floor | **KEEP** |

### E9 — Stale docs

| Item | Evidence | Verdict |
|------|----------|---------|
| Moved stubs | `docs/CLI.md:1-9`, `docs/DX.md`, `docs/FLOW.md`, `docs/internals/OWNERSHIP.md` | **KEEP** — link law. INDEX.md:117 already labels the stub. **DO NOT** delete (PR #67) |
| START_HERE lists `App.mount` then denies product path | START_HERE.md:27 vs :88 | **KEEP** — Cut 4 leftover-teach |
| CHANGELOG Unreleased still names channel pin `15cb1ed` | CHANGELOG.md:20 | **DO** with P0 pin bump (same-commit) |
| CHANGELOG claims compose tip `6d61c9e` | CHANGELOG.md:215 | **DO** with P1 self-pin |

### E10 — Channel pin honesty vs Cut C

Delta `15cb1ed` → `985e58a` (empty `git diff` on `Channel.boot`, `FileStateStore`, `apply_host_adapter`):

- Cut A (`0383bc1`): leftover teaching + delete `host/_ch_g0.py`. Compose does not import that stub.
- Cut C (`985e58a`): `http_action_content_type_ok(None)` is `False`. Python HTTP `/action` requires declared JSON or form type.

Compose callers:

| Surface | Content-Type | Empty CT? |
|---------|--------------|-----------|
| `live_client.py:26,63-74` | stamps endpoint; Channel JS posts `application/ux-channel+json` | no |
| `tests/asgi_http.py:86-96` | `application/json` | no |
| `helpers.py` | no HTTP POST | n/a |
| `serve_dev.py` origin forward | preserves upstream headers | n/a |

**Verdict:** bumping the pin is leftover-teaching honesty, not a compose behavior change. Pattern = Cut 3 pin bump (`b0cc17d` → `15cb1ed`). Clarity = name Cut C; do not retouch Kit/helpers.

### E11 — Lockfiles / unused deps / CVEs

| Artifact | Status |
|----------|--------|
| `poetry.lock` / `uv.lock` / `Cargo.lock` / `package-lock.json` / `pnpm-lock.yaml` | **absent** — dep tree is VCS pins in `pyproject.toml` + `Makefile` + `scaffold.py` + `apps/nook/requirements.txt` |
| Root `requirements.txt` | absent (create-app emits one) |
| `cek-surface` | declared `pyproject.toml:29`; **zero** `import cek_surface` in this tree; doctor copy `doctor.py:383` names it | **KEEP** — Channel/cek-runtime required wrap; not a ghost extra |
| `cek-host` | imported `wire/cek.py:79` | **KEEP** |
| `fastapi` | `[dev]` extra; lazy `routing/fastapi.py` | **KEEP** |
| `starlette` | `[serve]` extra; `serve_dev.py` | **KEEP** |
| CVEs / outdated | **unverifiable** — no pip-audit / OSV / Dependabot job in this repo. Do not invent |

### E12 — Fail-closed leftover already shipped

Cut 3: `cli.py` argv-only; `serve_dev.py` starts Tailwind `--watch` + tunnel; `start_css_watcher=` gone (comment leftover-taught; `test_source_locks.py:230` asserts the string in comments). Serve synonyms fail-closed. Console script `uxcompose = ux_compose.cli:main` import-resolves (`test_cli_script_honesty.py:32-48`). On-disk packages = `dx` `kit` `routing` `wire` (`test_source_locks.py:211-230`). **DEAD** doors. **KEEP** teaching.

### E13 — Cheap leftover fail-closed (Phase 2 class)

No remaining Cut-C-class fail-open on a compose product HTTP door.

- argv `create` already exits 2 (`test_cli_help.py:66-72`). A nicer leftover sentence would be encyclopedia polish, not a dual door. **KEEP** (not E13 DO).
- Empty Content-Type is **channel-owned** and already Cut C. Compose does not POST without CT. **KEEP** (do not reimplement Channel preflight here).

**E13 DO row:** none. Phase 2 DOs are **P0 pin** (E7/E10) and **P1 self-pin** (E7).

### E14 — Fashion / restyle pressure

Open PR **#67** `fix(arch): honest module names, no shims (serve/ package)`:

| Was | Proposed | Law |
|-----|----------|-----|
| `serve_dev.py` | `serve/dev.py` | AGENTS.md / ARCHITECTURE folder law: **no `serve/` package** |
| `helpers.py` | `algebra.py` | public import churn |
| `optional_plan` / `optional_fade` / `optional_slide` | `rise_enter` / `fade_enter` / `slide_enter` | A8 public rename |
| Moved stubs | delete | Diátaxis link law |

**DO NOT.** Close or park #67. Same class as channel #29 overshoot (`cli/` dump).

### E15 — Cross-package contract

| Claim | Status |
|-------|--------|
| Isolation frozen imports | `test_source_locks.py:472-498` — `Channel`, `ChannelConfig`, `apply_host_adapter`, `Intent` only | **KEEP** |
| Cap door `Channel.boot` | wire/boot.py:75-78; AGENTS.md:145 | **KEEP** |
| Store Redis wins | ADR 0006; `serve_state.py`; doctor `scan_store_precedence` | **KEEP** |
| Health formats vs codecs | host.md; compose does not own Channel `/health` | **KEEP** |
| ux-dom extract | pin `e8be99a` serialize `__all__` has no extract-by-id | **KEEP** walker |
| Two `create-app`s | product vs channel demo | **KEEP** homonym |

---

## Ranked DO / KEEP / DEAD / DO NOT

### DO (Phase 2 — separate PRs)

| Pri | Concern | Evidence | Pattern | Clarity |
|-----|---------|----------|---------|---------|
| **P0** | Pin ux-channel `15cb1ed` → `985e58aee76ca683774c4d4d58ab30a1d3b6efee` lockstep pyproject / Makefile / scaffold / nook / `test_hard_deps.py` / scaffold integration / encyclopedia pin strings (AGENTS, README, OWNERSHIP, host.md, ADR 0006, doctor ≥ pin, `wire/cek.py` comment, `test_source_locks.py` 15cb1ed asserts) | `pyproject.toml:25`; AGENTS.md:145; `test_source_locks.py:524,579,596` | Cut 3 pin bump (#70) | Name Cut C; no Kit/helpers/HTTP code |
| **P1** | Refresh `COMPOSE_VCS_PIN` `6d61c9e` → `855d929767f512517e36ba49cd40ce0cd496b2e6` (main tip at inventory). Lockstep nook + `test_hard_deps.py:16` + integration `6d61c9e` asserts + CHANGELOG:215 | `scaffold.py:271`; `apps/nook/requirements.txt:1` | #56 pin-align | Self-pin tracks last merged main, not this PR’s merge SHA |

Do **not** combine P0 and P1. Do **not** fold encyclopedia rewrite beyond the pin strings the locks already require.

### KEEP

Fragment walker until ux-dom extract · two walkers `build()`/`mount` · doctor library argv · kit leftover import · `_common.py` · empty extras · `HAS_DOM` · Moved stubs · argv `create` unknown · serve synonym teaching · `_bridge` Exception swallow · FastAPI blank GET residual · `cek-surface` declared · Isolation frozen imports · Channel `ops/`/`enhance/` not compose doors · Kit catalog.

### DEAD (doors gone, teaching stays)

`start_css_watcher=` live param · serve `development`/`production`/`restart_channel` synonyms · `routing/adapters/` package · `cli/` / `serve/` / `services/` packages · argv `create` as a live verb.

### DO NOT

- Fashion `cli/` `serve/` `services/` `helpers/` `fragment.py` (PR #67).
- Clean Architecture overlay / sibling packages.
- Public rename (`optional_*`, `algebra.py`, `brand.py`).
- Docs-first INDEX/LAYERS encyclopedia without a code cut.
- Delete Moved stubs.
- Reimplement Channel empty-CT in compose.
- Merge the two `create-app`s.
- Kit Cut 2 / sixth product.
- Invent poetry/uv/npm lockfiles as a “fix” for missing scanners.

---

## Cut order (later PRs)

0. **This plan** (no code).
1. **P0** channel pin `985e58a` — one PR, lockstep + pin-string locks.
2. **P1** compose self-pin `855d929` — one PR.
3. Stop. Residuals in KEEP are not a third honesty mega-PR.

## Implementation notes (P0 / P1 only)

### P0. Channel pin Cut C

Files: `pyproject.toml`, `Makefile`, `src/ux_compose/scaffold.py`, `apps/nook/requirements.txt`, `tests/unit/test_hard_deps.py`, `tests/integration/test_scaffold_create_app.py`, `tests/unit/test_source_locks.py`, `AGENTS.md`, `README.md`, `docs/OWNERSHIP.md`, `docs/reference/host.md`, `docs/adr/0006-serve-dev-shared-store.md`, `src/ux_compose/doctor.py`, `src/ux_compose/wire/cek.py`, `CHANGELOG.md` Unreleased.

- Replace pin SHA with `985e58aee76ca683774c4d4d58ab30a1d3b6efee`.
- Encyclopedia tests that `assert "15cb1ed" in …` must assert the new short SHA (same-commit). Historical CHANGELOG entries that *record* Cut 3’s `15cb1ed` stay.
- Doctor floor copy: `pin ≥ 985e58a` (compose’s required channel is now Cut C).
- No `live_client.py` / helpers / Kit edits.

Verify: `PYTHONPATH=src:. python -m pytest tests/unit/test_hard_deps.py tests/unit/test_source_locks.py tests/integration/test_scaffold_create_app.py tests/unit/test_cli_script_honesty.py tests/test_cek_door.py tests/test_cold_isolation.py -q`

### P1. Compose VCS pin

Files: `scaffold.py` `COMPOSE_VCS_PIN`, `apps/nook/requirements.txt`, `test_hard_deps.py` `COMPOSE_SHA`, integration scaffold asserts, CHANGELOG.

Pin **inventory tip** `855d929767f512517e36ba49cd40ce0cd496b2e6`, not the merge commit of P1. Same #56 residual (create-app is always one honesty-cut behind HEAD after merge).

Verify: `PYTHONPATH=src:. python -m pytest tests/unit/test_hard_deps.py tests/integration/test_scaffold_create_app.py -q`

---

## Residuals after Phase 2

- Homemade `_fragment_for_target` until ux-dom owns extract (`e8be99a` still has none).
- `_bridge` / FastAPI `_live_instance` Exception swallows (product residuals; need characterization, not leftover-teach).
- `cek-surface` declared, not imported here.
- No poetry/uv/cargo/npm lockfiles; CVE posture unverifiable.
- Two `create-app`s; three `doctor`s; `wire/` homonym.
- Open showcase PRs (#30 Lumen) are not honesty cuts.
- PR #67 remains **DO NOT**.
- Compose self-pin will lag the merge SHA of P1 (accepted #56 residual).

## Kill list (honor on every follow-up)

Fashion `cli/` `serve/` `services/` · Clean Architecture drawers · sibling packages · public rename for cleanliness · docs-first encyclopedia · #29-style overshoot · inventing a nicer product.

## Appendix. One screen

```text
COMPOSE @ 855d929
  cli.py          argv only (Cut 3)          KEEP
  serve_dev.py    clocks (ADR 0005)          KEEP
  wire/           Isolation door             KEEP
  helpers.py      walker residual (Cut B)    KEEP
  kit/            ownable catalog            KEEP (no Cut 2)
  doctor.py       library + argv             KEEP

PINS
  channel  15cb1ed  →  985e58a (Cut C)       DO P0
  compose  6d61c9e  →  855d929 (+67)         DO P1
  dom/behavior/motion == main                KEEP

DO NOT
  PR #67 serve/ + optional_* rename
  fragment.py / helpers/ / cli/
```
