# TELOS + ponytail maturity map (after Soft 1–4)

> **PLAN-ONLY.** Projection, not law. Law stays
> [OWNERSHIP.md](../OWNERSHIP.md). Shape stays
> [ARCHITECTURE.md](../ARCHITECTURE.md). Test how-to stays
> [guides/TESTING.md](../TESTING.md).
>
> Do not restyle `cli/` / `serve/` / `services/` / `helpers/` /
> `fragment.py`. Do not invent a sixth product. Do not overlay Clean
> Architecture or feature folders. Do not cut Cap / Isolation / Cut C
> empty Content-Type. Do not invent load/chaos harnesses for vanity.
>
> **Verified 2026-09-12** vs compose `main` `24a182f` and live tips.

Prior snapshots (still open, now stale as inventory):
[#73](https://github.com/bitplorer/ux-compose/pull/73) Cut B,
[#76](https://github.com/bitplorer/ux-compose/pull/76) Soft queue S1–S4,
[#77](https://github.com/bitplorer/ux-compose/pull/77) after Soft 1+2.
This page supersedes those as the current tip map. Do not merge them
into one encyclopedia.

---

## 0. Status one-screen

| Layer | Compose pin | Fresh `origin/main` | Status |
|-------|-------------|---------------------|--------|
| **ux-compose** | `24a182f` (this tip) | same | current |
| **ux-channel** | `ae5a675` (Soft 1+2) | **`d0412c6`** Soft 4 | **rotting +2** |
| **ux-dom** | `e8be99a` | `e8be99a` | pin == tip |
| **ux-behavior** | `793f120` | `793f120` | pin == tip |
| **ux-motion** | `67ff3f0` | `67ff3f0` | pin == tip |
| **cek-host / cek-surface** | `>=0.1.3` | PyPI **0.1.3** (`cek-python` `cd101a7`) | floor met |

Channel Soft 1–4 are **DONE** on tip `d0412c6`:

| Soft | SHA | What | Status |
|------|-----|------|--------|
| S1 | `b0a68d8` #34 | HTML lower → ux-dom when present | shipped |
| S2 | `ae5a675` #35 | `uxchannel create-app` lab honesty | shipped |
| S3 | `dd2ce75` #36 | kit / `ChannelComponent` leftover-teach | shipped |
| S4 | `d0412c6` #37 | `render/response.py` → `ux_dom.response` | shipped |

**Cap `mount_channel` KEEP.** Soft queue is **empty of S1–S4**. No Soft 5
is evidenced. Next honesty is the **compose pin**, not a new product
surface.

`COMPOSE_VCS_PIN` `957f81f` vs HEAD `24a182f` is the #56 chicken-egg
(+ #78). Not a fail-closed hole.

---

## 1. TELOS + ponytail

A layer's **telos** is the end it exists to serve. Callers **USE** that
end. Re-implementing it elsewhere is bloat even when the clone is thin.

| Layer | Telos (owns) | Must not own |
|-------|--------------|--------------|
| **ux-dom** | Tree → HTML (`__render__` / `to_html_bytes`), `Document` shell, package static, `uxdom` | Product CLI, Tailwind compiler, `WebAssets`, Clock A, HMR, Intent/Cap, MorphState |
| **ux-behavior** | Product meaning → verified `list[Op]`; `MorphState` / `@action` | Raw HTML, wire codecs, Cap crypto, product serve |
| **ux-channel** | Intent → Cap → Result; wire; Cap Host (cek-runtime); `StateStore`; Cap HTTP `mount_channel` | HTML trees, CSS, Document serialize, product `uxcompose` / Clock A |
| **ux-motion** | Presence / transition plans as data (IR v1) | `@action`, Document construction, Cap mint, product CLI |
| **cek-host** | Cap mint / verify / project (authority) | HTTP Product host (Clock A), ux-dom trees |
| **cek-surface** | Surface / Peer IR / carriers | ux-channel wire; a second Cap machine |
| **ux-compose** | Author composition + `uxcompose` + Tailwind + `WebAssets` + Clock A + `wire/` | Re-implementing any specialist |
| **FastAPI / Starlette** | HTTP process, `HTMLResponse` / JSON / WS | Channel protocol, Document serialize |

**Ponytail** (shrink only in this order — never reverse):

1. **YAGNI** — delete the unused plane if no locked L depends on it.
2. **Reuse the owner** — call the specialist / host framework.
3. **stdlib** — `html.parser`, `sqlite3`, `re` only when the owner has no public API yet.
4. **Minimum local** — smallest adapter that keeps Isolation + leftover teaching.

Organize by **capability / happy path**, not by `services/` or feature
folders. One taught path per job.

---

## 2. Dep tree (pins + transitive)

```text
ux-compose @ 24a182f
├── ux-dom @ e8be99a
│   ├── Jinja2, valio, marko, anyio, typer
│   └── [optional] fastapi, uvicorn, pytailwindcss, watchfiles
├── ux-behavior @ 793f120          (zero hard deps)
├── ux-motion @ 67ff3f0            (zero hard deps)
├── ux-channel @ ae5a675  → tip d0412c6
│   ├── itsdangerous
│   ├── cek-host >=0.1.3
│   └── cek-surface >=0.1.3 → cek-host
│   peer: ux-dom (glue / Soft 1+4 prefer; not a hard dep)
│   KEEP: ux_channel_ux_dom glue; asgi.mount_channel
├── cek-host>=0.1.3                (zero hard deps)
└── cek-surface>=0.1.3
compose extras: [serve] uvicorn watchfiles httpx starlette websockets
                [dev]   pytest* + fastapi + serve stack
```

No compose `poetry.lock` / `uv.lock` / root `requirements.txt`. Pins
are VCS SHAs in `pyproject.toml` + `Makefile` + `scaffold.py` +
`apps/nook/requirements.txt`. That absence is policy, not a hole.
CVEs unverifiable (no pip-audit / OSV job). Do not invent lockfiles.

**Not in this tree:** `ux-fnbase`, retired `ux-app`, `cek-framework`
(law), `harbor`. `cek-runtime` is Channel's default decide, not a
compose pip pin (`wire/cek.py` only).

Floor split: product **≥3.14**; channel / behavior / motion / cek still
advertise 3.10. Not a compose Soft.

---

## 3. Capability × owner × re-implement risk

One taught path per happy path. **Risk** is “a sibling still clones or
teaches a second door.” Soft 1–4 moved channel HTML/kit/create-app/
response from OWNER-WRONG **live** to leftover-teach + prefer-owner.

| # | Happy path (taught) | Owner | Compose door | Re-implement risk | Verdict |
|---|---------------------|-------|--------------|-------------------|---------|
| C1 | Author `render()` tree → HTML | **ux-dom** `to_html_bytes` | `helpers._serialize_tree` (`helpers.py:112-118`) | Channel leftover `lower_html` / `to_html` (Soft 1 prefer-owner) | **KEEP** USE owner |
| C2 | Extract `#id` from serialized HTML | **ux-dom** (missing on serialize `__all__` @ `e8be99a`) | homemade `_fragment_for_target` (`helpers.py:121-124`, walker `:166+`) | Channel `_guess_target_from_html` | **KEEP** until ux-dom extract. No `fragment.py` |
| C3 | Offline MorphState / `@action` | **ux-behavior** | `component.py` re-export; `App.boot` L1 | none in compose | **KEEP** |
| C4 | Product scaffold | **ux-compose** `uxcompose create-app` | `scaffold.py` | `uxchannel create-app` leftover-taught (Soft 2); `cek create-app` orthogonal | **KEEP** homonym |
| C5 | Clock A page GET | **ux-compose** + FastAPI | `build()` → `routing/fastapi.py` | ux-dom leftover `DirectoryRouter`; atelier handmade `HTMLResponse` | **KEEP** product door. Park atelier |
| C6 | Payload → media type | Clock A spec | `dict` JSON / generator stream / tree HTML (`routing/fastapi.py:118+`) | FastAPI `default_response_class`, `StreamingRoute` | **DEAD** leftovers. **KEEP** teaching |
| C7 | Live Intent / Cap | **ux-channel** Cap Host | `App.use_channel` → `wire/boot.py` `Channel.boot` (`:75-84`) | `ActionRegistry.from_config` as compose import | **KEEP**. Frozen wire: `Channel`, `ChannelConfig`, `apply_host_adapter`, `Intent` |
| C8 | Cap HTTP `/action` | **ux-channel** `mount_channel` | compose does not remount; origin forwards | Gutting `asgi/fastapi.py` “to slim” | **KEEP** owner door. Fat extras ≠ the door |
| C9 | Morph fragment (no shell/brand) | compose walker + behavior Ops | `update_with` + `_fragment_for_target` | Full-document `render()` (CTO FullShellHello) | **KEEP** walker; authors write fragments |
| C10 | Motion enter / play | **ux-motion** IR v1 | `app.use_motion()`; `__all__` `scene`/`fade`/`rise`/`slide` | Channel `transition.*` | **KEEP**. Channel must not learn motion |
| C11 | `serve dev` three clocks | **ux-compose** ADR 0005 | `cli.py` argv; `serve_dev.py` spawn | in-process HMR hub; CSS `Popen` in `hmr.py`; `--one-process` | **KEEP**. Clocks not collapsed |
| C12 | Session bag | **ux-channel** `FileStateStore` / Redis | `serve_state.py` lifecycle only | compose-owned store class | **KEEP**. Redis wins. Doctor `scan_store_clone` |
| C13 | Tailwind / app CSS | **ux-compose** `tailwind.py` + `WebAssets` | `uxcompose build` | ux-dom `TailwindCommand` / stub `WebAssets` | **KEEP** fail-closed stubs on dom |
| C14 | Ownable kit | **ux-compose** `kit/` + `uxcompose add` | `kit/copy.py`; `kit_construct.py` next to `Component` | channel `components/` leftover-taught (Soft 3); `from ux_compose.kit import` in apps | **KEEP**. Do not port channel kit here |
| C15 | Doctor / isolation | **ux-compose** `doctor` library | `from ux_compose import doctor` + `uxcompose doctor` | `uxchannel` / `uxdom` / `uxbehavior` doctors | **KEEP** homonym. argv delegates to library |
| C16 | HMR morph-then-reload | **ux-compose** `hmr.py` | WS `/__uxcompose/hmr` | `Document.use` HMR; ux-dom `reloader/` | **KEEP**. HTML insert is middleware |
| C17 | Response HTML helpers | **ux-dom** `ux_dom.response` | Clock A already `ux_dom.response.starlette` (`routing/fastapi.py:88`, `:105`) | channel leftover clone (Soft 4 prefer-owner) | **KEEP**. Soft 4 is channel, not this file |
| C18 | Cap Host identity | **cek-host** via channel | `wire/cek.py` `apply_host_adapter` (`:113-114`) | classic `CapService` when `cek=require` | **KEEP**. Floor comment `channel ≥ 985e58a` |
| C19 | Deploy checklist | **ux-compose** `deploy.py` | `uxcompose deploy` | product CLI on uxdom | **KEEP** |

**Re-implement risk after Soft 1–4:** live OWNER-WRONG HTML/response/kit
on channel is leftover-teach + prefer-owner. Residual risk is agents
re-promoting those leftovers, or gutting `mount_channel`. Compose's
own residual is still C2 (walker) until ux-dom extract.

---

## 4. Residual dual doors / bloat

TELOS tags: **E5** two ways to do one job · **E13** residual that holds
locked L · **E14** do not invent surface to “clean up.”

### 4.1 E5 — dual doors (keep product; leftover-teach the other)

| Taught path (KEEP) | Other door | Close how |
|--------------------|------------|-----------|
| `build()` | Teaching `App.mount` as product path | Already leftover-teach: mount = catalog scan (`ARCHITECTURE.md:206-208`) |
| `scan_surfaces` + `DirectoryRoutes.discover` | Merge the walkers | **Forbidden** |
| `Channel.boot` via `wire/` | `ActionRegistry.from_config` compose import | Keep teaching; do not add the import |
| `mount_channel` Cap HTTP | Fat FastAPI extras in `asgi/fastapi.py` | Soft later; **not** one Soft to gut the file |
| `uxcompose create-app` | `uxchannel create-app` (Soft 2 leftover) | Honesty shipped. Do not merge CLIs |
| Frozen serve `dev`/`prod`/`restart-channel` | argv `development`/`production`/`restart_channel` | Already exit 2 |
| `from ux_compose import div` | `from ux_compose.kit import` in apps | Doctor teaching; `uxcompose add` |
| Document `Channel.optional()` | `live_client.attach_live_client` | Teach Document path; do not delete until tests migrate |
| Clock A `build()` GET | atelier `apps/*/server.py` handmade `HTMLResponse` | Parked. Not one Soft (`pulse/server.py:48`) |

### 4.2 E13 — KEEP (deleting drops L)

| Residual | Why | Lock |
|----------|-----|------|
| `_fragment_for_target` | ux-dom serialize `__all__` has no extract-by-id | `helpers.py:121-124`; `test_source_locks.py:108-135`; `CRITIC.md:35` |
| `DirectoryASGI` | Clock A degrade when FastAPI absent | `routing/asgi.py`; `test_host.py` |
| `serve_state.py` sqlite `DELETE` | Isolation: origin must not import `ux_channel` | ADR 0006; `test_serve_state.py` |
| `bind_pages` / `include_directory_router` alias | Signature lock | `test_hard_cut_ownership.py:94-98` |
| Two walkers inside `build()` | Catalog ≠ HTTP path law | `test_source_locks.py:448-469` |
| `mount_channel` | Owner Cap HTTP ≠ Clock A | channel Soft 2/4 leftover table + gate |
| `ux_channel_ux_dom` glue | Optional interop; neither core imports the other | channel package init |
| Leftover *names* in doctor/docs | Teaching tokens | `ARCHITECTURE.md` leftover tables |
| `COMPOSE_VCS_PIN = 957f81f` | Pin-bump cannot pin itself | `test_hard_deps.py:16` |
| Channel leftover clones (HTML / response / kit / lab create-app) | Soft 1–4 leftover-teach; tests lock prefer-owner | channel `tests/gate` @ `d0412c6` |

**E13 DO (cheap leftover fail-closed on a compose HTTP door):** **none.**
Empty Content-Type is channel Cut C. argv `create` already exits 2.

### 4.3 Parked (characterization, not Soft)

| Site | Evidence | Why not a cut |
|------|----------|---------------|
| `_live_instance` `except Exception` | `routing/fastapi.py:62-68` | Blank GET is product behavior |
| `wire/boot._bridge` `except Exception` | `boot.py` bridge register | Needs cap-bridge characterization |
| atelier handmade `HTMLResponse` | `apps/pulse/server.py:48`; shop/studio siblings | Showcase leftover vs `build()`. Not one Soft |
| `cek-surface` declared, not imported here | `pyproject.toml:29` | Channel/cek-runtime wrap |
| Unused pytest markers `slow` / `live` | `pyproject.toml:61-64`; zero uses | Marker drift. Do not invent suites to justify them |
| CI no `--cov-fail-under` | TESTING.md suggests 40; `.github/workflows/ci.yml` is plain pytest | Policy suggestion, not a rotting lock |

### 4.4 Bloat that is already DEAD (teaching stays)

`start_css_watcher=` live param · serve synonyms · `routing/adapters/` ·
`cli/` / `serve/` / `services/` packages · argv `create` as a live verb ·
HTML-string kit fallbacks · Document-absent product path · optional
specialist extras as unlock ladder.

---

## 5. Test-lock matrix

Legend: **L** = claimed locked behaviour · **lock** = a test that would
fail if L moved · **E3** = implemented / claimed, not locked.

Compose tree: 75 test modules, ~430 `test_*`. Channel tip: 204 under
`python/tests/` (default `tests/gate`, 34 gate modules). ux-dom: 94
numbered suites. behavior: 27. motion: 7. Compose **`tests/property/`
is dropped** (`ARCHITECTURE.md:197`; `test_source_locks.py`).

### 5.1 Compose layers vs claimed L

| Capability (L) | Layer exists | Lock exists | E3 gap |
|----------------|--------------|-------------|---------|
| Isolation: cold import never pulls wire | `tests/test_cold_isolation.py`, `tests/security/` | AST + `scan_isolation` + `__init__` no `ux_channel` | **none** |
| Isolation: product AST no `ux_channel` | same + `test_source_locks.py:472-498` | frozen import allowlist | **none** |
| Cap mint / Intent 401 without cap | `tests/feature/test_cto_cap_mint_fail_closed.py`, `tests/unit/test_control_cap_mint.py` | CTO + unit | skipif without channel (honest) |
| Fragment law / no shell in morph | `tests/feature/test_cto_fragment_law.py` (`cto_red`) | FullShellHello + scaffold | **none** (walker is the lock) |
| Clock A payload / path / wrap | `tests/unit/test_host.py` | 30 tests; `App.mount` wrap parity | **none** |
| Two walkers, one product door | `test_source_locks.py:448-469` | source lock | **none** |
| `Channel.boot` / no silent cfg | `test_source_locks.py:37-55` | fail-closed strings | **none** |
| Store: no compose `StateStore` class; Redis wins | `test_serve_state.py`, `test_doctor_laws.py`, ADR lock | doctor + source | **none** |
| Hard-dep pins lockstep | `test_hard_deps.py` | pyproject / Makefile / scaffold / nook / CI 3.14 | **P0:** lock still names `ae5a675`, not tip `d0412c6` |
| Soft 1+2 encyclopedia pin speech | AGENTS / OWNERSHIP / host / ADR 0006 | `test_source_locks.py:567-598` locks Cut C `985e58a` + `Channel.boot`, **not** Soft 3+4 | **P0 same-commit:** pin strings still say Soft 1+2 |
| Serve argv frozen verbs | `test_cli_help.py` | synonyms + clock flags fail-closed | **none** |
| Console script `ux_compose.cli:main` | `test_cli_script_honesty.py` | no `cli/` package | **none** |
| Folder law / no `fragment.py` | `test_source_locks.py` | kit_construct + packages `dx kit routing wire` | **none** |
| `__all__` author / host / motion | `test_architecture_public_api.py` | REQUIRED / ADDED / HOST; no `maybe_*` | **none** |
| HMR: no hub / watcher / Popen | `test_hmr.py` | path + source | **none** |
| CSS watch in `tailwind.py` | `test_source_locks.py:425-445` | not in `cli`/`hmr` | **none** |
| Scaffold create-app Document path | `tests/integration/test_scaffold_create_app.py` + CTO hello | layout + pins ≥ `ae5a675` | pin floor rotting (same P0) |
| Kit copy / `kit_construct` import | `test_cli_add.py`, `test_kit_construct.py` | copy rewrite law | **none** |
| Kit APG / stems | `tests/test_kit_*.py` | render + roles | not a dual door |
| Brand wrap GET=1 morph=0 | `test_cto_brand_wrap.py` | feature | **none** |
| L0–L3 zero-rewrite | `test_progressive_unlock.py` | same Component | **none** |
| Morph-then-Play XOR | `test_xor_helpers.py`, `test_morph_then_play.py` | helpers | **none** |
| CEK door / Cap Host identity | `test_cek_door.py`, `test_build_cek.py` | `CekHostCapService` | **none** |
| Hard-cut: product CLI not on uxdom | `tests/regression/test_hard_cut_ownership.py` | help + WebAssets + DirectoryRoutes | **none** |
| Parallel dispatch correctness | `tests/concurrency/test_parallel_dispatch.py` | **crash-only** (`:27-38`) | **theatre.** No ordering L claimed. Do not expand |
| Load / stress SLO | `tests/load/test_stress_dispatch.py` | 1000 bumps **< 15s** (`:27-35`) | **theatre.** No fail-closed hole. Do not expand |
| Security / pen-style | `tests/security/test_isolation_and_sanitize.py` | 3 tests (import + pulse `_clean_args` + HMR path) | defensive unit. Not a missing SLO |
| Resilience matrix | `tests/resilience/test_ownership_flow.py` | OWNERSHIP text + aliases | Phase 1 residual. Do not invent soak |
| Property / Hypothesis | **absent** (dropped) | absence locked | **KEEP dropped.** Channel gate owns Hypothesis |
| Coverage fail-under 40 | TESTING.md suggestion | **CI does not run cov** | not a rotting behaviour lock |
| Pulse live HTTP matrix | `test_pulse_live.py` | build + doctor API only | showcase smoke. Not E13 |
| Channel Soft 3+4 prefer-owner | **channel** `tests/gate` @ `d0412c6` | `test_html_owner_ux_dom.py`, `test_response_owner_ux_dom.py`, encyclopedia leftover | compose must not re-lock channel internals. **Pin** so CI installs those gates |
| ux-dom extract-by-id | **absent** @ `e8be99a` | compose walker KEEP lock | owner gap, not compose Soft |

### 5.2 Specialist test posture (do not copy into compose)

| Repo | Suites | What they lock | Do not invent here |
|------|--------|----------------|--------------------|
| ux-channel @ `d0412c6` | gate 34 + core + asgi + stress + security | PUBLIC_API_FREEZE, leftover Soft 1–4, `mount_channel` KEEP, Cut C empty CT | compose `tests/gate/` or property tree |
| ux-dom @ `e8be99a` | `01_core`…`07_resilience` (incl. `05_chaos`) | serialize, Document, fail-closed product stubs | compose chaos suite (dom already claims it) |
| ux-behavior @ `793f120` | flat + resilience | MorphState / `@action` / doctor | clone Behavior tests |
| ux-motion @ `67ff3f0` | unittest discover | IR v1 / MotionChannel | Channel `transition.*` tests |
| cek-python 0.1.3 | host/surface doctors | Cap authority | second Cap machine in compose |

**Load / chaos rule:** only if already claimed or a real fail-closed
hole. Compose load/concurrency do **not** claim a fail-closed L.
ux-dom `05_chaos` is that layer's claim. **DO NOT** add compose chaos
or raise the 15s budget into an SLO.

### 5.3 Coverage vs TESTING.md

| Claim (`docs/guides/TESTING.md`) | Reality |
|----------------------------------|---------|
| Layers unit / feature / regression / integration / concurrency / load / security / legacy | dirs exist |
| `tests/property` | dropped; locked |
| markers `slow` / `live` / `cto_red` | only `cto_red` used; live = skipif |
| CI `--cov-fail-under=40` | **not in CI**; Makefile `coverage` has no fail-under |
| Pulse as live showcase | integration build/doctor only |

E3 that is **not** a DO: unused markers, missing cov gate, pulse HTTP
thinness. Prefer missing **locks on rotting pins** over new suites.

---

## 6. Ranked DO / KEEP / DEAD / DO NOT

### DO (Phase 2 — separate PRs, one concern)

| Pri | Concern | Evidence | Pattern | Clarity |
|-----|---------|----------|---------|---------|
| **P0** | Pin ux-channel `ae5a675` → `d0412c62b5180f69e76d16c913809f6c34dee269` lockstep pyproject / Makefile / scaffold / nook / `test_hard_deps.py` / scaffold integration / encyclopedia pin strings (AGENTS, README, OWNERSHIP, host.md, ADR 0006). Cut C floor `985e58a` **stays**. Name Soft 1–4 on tip. | `pyproject.toml:25`; `Makefile:10`; `scaffold.py:267`; `test_hard_deps.py:13`; `test_scaffold_create_app.py:103,180`; `AGENTS.md:145-146`; `docs/OWNERSHIP.md:80`; `docs/reference/host.md:226-227`; `docs/adr/0006-serve-dev-shared-store.md:53-54` | #78 pin bump | Soft 3+4 already on tip. No Kit/helpers/HTTP. No `mount_channel` touch |
| **P1** | Refresh `COMPOSE_VCS_PIN` `957f81f` → inventory `main` tip after P0 merges (`24a182f` is stale the moment P0 lands). Lockstep nook + `test_hard_deps.py:16` + integration `957f81f` asserts | `scaffold.py:271`; `apps/nook/requirements.txt:1` | #75 / #56 | Self-pin tracks last merged main, not this PR’s merge SHA |

Do **not** combine P0 and P1. Do **not** fold encyclopedia rewrite
beyond the pin strings the locks already require.

**No E13 DO.** No Soft 5.

### KEEP

Fragment walker until ux-dom extract · `mount_channel` · Clock A +
serve-dev clocks · two walkers · `Channel.boot` via `wire/` ·
FileStateStore owner · Redis wins · kit catalog + `kit_construct` at
root · doctor library argv · leftover teaching tables · empty extras ·
`HAS_DOM` · Moved stubs · Isolation AST · channel leftover clones
(prefer-owner) · `ux_channel_ux_dom` · dropped `tests/property` ·
theatre load/concurrency as residual smoke (do not grow) · PR #67
parked.

### DEAD (doors gone, teaching stays)

`start_css_watcher=` live param · serve synonyms · `routing/adapters/` ·
ghost `cli/` `serve/` `services/` · argv `create` · Document-absent
path · kit HTML-string fallbacks · Soft 1–4 as an *open* channel queue.

### DO NOT (kill list — honor on every follow-up)

- Fashion restyle: `cli/` `serve/` `services/` `helpers/` `fragment.py` (PR **#67**).
- Clean Architecture / hexagonal `ports/` / feature-folder drawers.
- Sixth product (`ux-app`, compose-host, channel-http, a second kit).
- Docs-first encyclopedia / INDEX rewrite without a code cut.
- Trust-boundary cut: Isolation AST, Cap mint, Cut C empty CT, CSRF, `present_cap_must_verify`.
- Gut `asgi/fastapi.py` or delete `mount_channel`.
- Merge Clock A GET with Channel `/action` or CEK Host.
- Re-lock channel Soft 1–4 internals as compose tests.
- Invent load/chaos/property harnesses for vanity.
- Public rename (`optional_*`, `algebra.py`).
- Delete Moved stubs.
- Merge the two `create-app`s.
- Invent poetry/uv lockfiles as a “CVE fix.”
- Port channel `components/` into compose `kit/`.

---

## 7. Soft order

| # | Status | Next |
|---|--------|------|
| S1–S4 | **empty** (shipped on channel `d0412c6`) | none |
| Compose pin | **P0** (this map) | after this plan |
| Compose self-pin | **P1** | after P0 merge |
| ux-dom extract-by-id | parked owner gap | not a compose Soft; walker stays |
| `live_client` retire | parked | tests still use insert |
| atelier `HTMLResponse` | parked | not one Soft |
| FastAPI `_live_instance` swallow | parked | characterization |

Stop after P0 (+ P1 later). Residuals in KEEP are not a mega-PR.

---

## 8. Pattern / Clarity gate (any later cut)

A DO row ships only when **both** pass:

| Test | Pass | Fail |
|------|------|------|
| **Pattern** | Matches leftover-teach / fail-closed / pin-lockstep (#70, #74, #78, channel Soft 1–4) | New folder, new public name, new product door, new test *layer* |
| **Clarity** | Names the leftover; one concern; same-commit lock | Encyclopedia-only, or “while we’re here” |

Ponytail on every cut: YAGNI → reuse owner → stdlib → minimum local.

**Stop / revert if:** Isolation AST red · leftover-teaching red · new
root `__all__` · `mount_channel` removed · `fragment.py` added ·
`serve/` package.

---

## 9. Implementation notes (P0 only)

Files: `pyproject.toml`, `Makefile`, `src/ux_compose/scaffold.py`,
`apps/nook/requirements.txt`, `tests/unit/test_hard_deps.py`,
`tests/integration/test_scaffold_create_app.py`, `AGENTS.md`,
`README.md`, `docs/OWNERSHIP.md`, `docs/reference/host.md`,
`docs/adr/0006-serve-dev-shared-store.md`, `CHANGELOG.md` Unreleased.

- Replace current pin with `d0412c62b5180f69e76d16c913809f6c34dee269`.
- Encyclopedia: “Soft 1–4 on tip”; Cut C floor stays `985e58a`.
- Doctor copy `pin ≥ 985e58a` **stays** (behavior floor, not Soft 3+4).
- Historical CHANGELOG rows that *record* #78 `ae5a675` stay.
- No `live_client.py` / helpers / Kit / `routing/` edits.

Verify:

```bash
PYTHONPATH=src:. python -m pytest \
  tests/unit/test_hard_deps.py \
  tests/unit/test_source_locks.py \
  tests/integration/test_scaffold_create_app.py \
  tests/unit/test_cli_script_honesty.py \
  tests/test_cek_door.py \
  tests/test_cold_isolation.py -q
```

---

## Appendix. One screen

```text
COMPOSE @ 24a182f
  build()         Clock A product door     KEEP
  wire/           Isolation / Channel.boot KEEP
  helpers.py      walker until dom extract KEEP
  kit/            ownable catalog          KEEP
  mount_channel   Cap HTTP (channel)       KEEP

SOFT 1–4          done on channel tip      EMPTY QUEUE
PINS
  channel  ae5a675 → d0412c6 (Soft 1–4)    DO P0
  compose  957f81f → after P0 tip          DO P1 later
  dom/behavior/motion == main              KEEP

TESTS
  Isolation / Clock A / CTO / pins         LOCKED
  property                                 DROPPED (KEEP)
  load / concurrency                       THEATRE — do not grow
  channel Soft 3+4 gates                   on tip; pin to install

DO NOT
  PR #67 serve/ · sixth product · chaos theatre
  gut mount_channel · docs-first restyle
```
