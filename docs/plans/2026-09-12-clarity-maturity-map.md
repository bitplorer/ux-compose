# TELOS Phase 0–1 — clarity / denoise / maturity map

> **PLAN-ONLY.** Projection, not law. Law stays
> [OWNERSHIP.md](../OWNERSHIP.md). Shape stays
> [ARCHITECTURE.md](../ARCHITECTURE.md). Test how-to stays
> [guides/TESTING.md](../TESTING.md).
>
> Phase 0–1 cartograph only. No product code. No fashion restyle.
> No folder taxonomy overlay. No E14 new public surface.
> No A8 rename unless a named lie. Clarity Test / Pattern Test
> **KEEP-on-fail**.
>
> Cap / `mount_channel` / `Channel.boot` via `wire/` **KEEP**.
> Walker escape **KEEP**. No `fragment.py`. PR **#67** `serve/`
> restyle parked. Valio out of scope.
>
> **Verified 2026-09-12** vs compose `origin/main` `fb7a125`
> (`docs(plans): TELOS tip e65971b ownership/usage Soft DO (#84)`)
> and live specialist tips fetched the same hour.

Prior snapshot
[docs/plans/2026-09-12-tip-e65971b-ownership.md](2026-09-12-tip-e65971b-ownership.md)
(#84) emptied the **OWNER-WRONG** Soft queue. This page is a
**new tip map** for **CLARITY / DENOISE / MATURITY / test-lock
strength** inside Framework Lock. It does not merge stale
inventories **#73 / #76 / #77 / #80**. Do not reopen them.

Softs only if: ambiguity down (synonym / dual / shadow / stale-doc)
**or** fail-open → fail-closed **or** claimed-false → true+lock
**or** unused export / dead path with an absence lock.
LoC / file-count renames are **not** Softs.

**Soft queue after this inventory: empty.**

---

## 0. Status one-screen

| Layer | Compose pin (SSOT) | Fresh `origin/main` | Status |
|-------|--------------------|---------------------|--------|
| **ux-compose** | tip `fb7a125` | `fb7a12557146e88266ec5fa6d437f2d3104489e5` | current |
| **ux-channel** | `d0412c62b5180f69e76d16c913809f6c34dee269` | **same** | pin == tip (Soft 1–4) |
| **ux-dom** | `2e894cd7bca66e1da6c2f9d42b2d1a8bb937c92c` | `d107209` (**+1 docs-only**) | product pin current |
| **ux-behavior** | `793f120e3b1388925772cd069b070d7918b78baa` | **same** | pin == tip |
| **ux-motion** | `67ff3f0c4912b70b7056f8226a6f226b6fe93f60` | **same** | pin == tip |
| **cek-host / cek-surface** | `>=0.1.3` | PyPI **0.1.3** (latest) | floor met |
| **cek-runtime** | not a compose pip pin | `f384448` | Channel decide; `wire/cek.py` only |

Delta vs #84 (`e65971b`): **one commit** — this ownership plan.
Product files, pins, and specialist tips are unchanged.

**Already landed (do not re-do):**

| Cut | SHA / PR | What |
|-----|----------|------|
| Channel Soft 1–4 | tip `d0412c6` #34–#37 | prefer ux-dom HTML/response; create-app lab honesty; kit leftover-teach |
| Channel pin | compose #79 | lockstep `d0412c6` |
| ux-dom `extract_by_id` | `2e894cd` ux-dom #20 | owner serialize `__all__` |
| Compose C2 Soft USE | `e65971b` #83 | `helpers._fragment_for_target` prefers owner; walker KEEP as escape |
| Ownership Soft DO | `fb7a125` #84 | OWNER-WRONG queue empty |

`COMPOSE_VCS_PIN` `24a182f` vs HEAD `fb7a125` is the #56 chicken-egg
(create-app cannot pin the merge SHA of the PR that bumps it). Not a
clarity hole. **KEEP**, not a third honesty PR.

ux-dom tip `d107209` is **plan-only** (ux-dom #19). Product extract
already shipped on the pin. Pinning compose to that SHA is YAGNI.
**KEEP** `2e894cd`.

---

## 1. TELOS + ponytail + this-pass bar

A layer's **telos** is the end it exists to serve. Callers **USE** that
end. Re-implementing it elsewhere is bloat even when the clone is thin.

| Layer | Telos (owns) | Must not own |
|-------|--------------|--------------|
| **ux-dom** | Tree → HTML (`__render__` / `to_html_bytes`), `Document` shell, package static, `extract_by_id`, `uxdom` | Product CLI, Tailwind compiler, `WebAssets`, Clock A, HMR, Intent/Cap, MorphState |
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

**Intent Vector** (required on every DO Soft; none in this queue):

| Field | Meaning |
|-------|---------|
| **Intent** | One capability end (the telos being served) |
| **Vector** | Owner library → compose/channel USE site (`path:line`) |
| **Concern** | One Soft; prefer reuse-owner / leftover-teach / fail-closed over rename |
| **Not** | Folder move, public rename, encyclopedia, sixth product |

**Clarity / Pattern gate (KEEP-on-fail):**

| Test | Pass | Fail |
|------|------|------|
| **Pattern** | leftover-teach / fail-closed / pin-lockstep / prefer-owner | new folder, new public name, new product door, new test *layer*, LoC rename |
| **Clarity** | names the leftover; one concern; same-commit lock | encyclopedia-only, or “while we’re here” |

---

## 2. Dep cartograph — pins vs tips (pasted evidence)

### 2.1 Tree @ `fb7a125`

Folders are import/copy laws. On-disk packages:

```text
src/ux_compose/
  dx/          slang leftover (probe.py)     KEEP
  kit/         ownable catalog (85 widgets)  KEEP
  routing/     Clock A host pair             KEEP
  wire/        only ux_channel / CEK door    KEEP
  *.py         library ∩ CLI (37 files)      KEEP
```

Ghost absences (this write):

```text
ABSENT src/ux_compose/cli
ABSENT src/ux_compose/serve
ABSENT src/ux_compose/services
ABSENT src/ux_compose/helpers/          (helpers.py is a module)
ABSENT src/ux_compose/fragment.py
ABSENT tests/property
ABSENT docs/MODULE_MAP.md
```

69 `tests/test_*.py` modules. Isolation AST: no `from ux_channel` /
`import ux_channel` outside `wire/` (comment-only hit in
`helpers.py:4`).

### 2.2 SSOT lockstep (compose tree @ `fb7a125`)

`pyproject.toml:24-29`:

```text
ux-dom     @ git+https://github.com/bitplorer/ux-dom.git@2e894cd7bca66e1da6c2f9d42b2d1a8bb937c92c
ux-channel @ git+https://github.com/bitplorer/ux-channel.git@d0412c62b5180f69e76d16c913809f6c34dee269#subdirectory=python
ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git@793f120e3b1388925772cd069b070d7918b78baa
ux-motion  @ git+https://github.com/bitplorer/ux-motion.git@67ff3f0c4912b70b7056f8226a6f226b6fe93f60
cek-host>=0.1.3
cek-surface>=0.1.3
```

`Makefile:8-11` — same four SHAs (`UX_*_SHA`).

`src/ux_compose/scaffold.py:267-271`:

```text
CHANNEL_VCS_PIN  = d0412c62b5180f69e76d16c913809f6c34dee269
BEHAVIOR_VCS_PIN = 793f120e3b1388925772cd069b070d7918b78baa
MOTION_VCS_PIN   = 67ff3f0c4912b70b7056f8226a6f226b6fe93f60
DOM_VCS_PIN      = 2e894cd7bca66e1da6c2f9d42b2d1a8bb937c92c
COMPOSE_VCS_PIN  = 24a182f35e3d0743a2faafddb5ba0396324b2d9a
```

`apps/nook/requirements.txt:1-7` — same compose self-pin + four
specialist SHAs + `cek-*>=0.1.3`. Other atelier apps have **no**
`requirements.txt` (Makefile `shop`/`studio`/`pulse` run via
`PYTHONPATH=src:.`).

`tests/unit/test_hard_deps.py:12-16` locks those SHAs +
`COMPOSE_SHA = 24a182f…`. CI (`.github/workflows/ci.yml`) is
`pip install -e ".[dev]"` — no second pin list.

Fresh `git ls-remote` (this write):

```text
ux-compose  HEAD  fb7a12557146e88266ec5fa6d437f2d3104489e5
ux-channel  HEAD  d0412c62b5180f69e76d16c913809f6c34dee269
ux-dom      HEAD  d107209d5d61dca6a832f83511af46887c5ae9eb
ux-behavior HEAD  793f120e3b1388925772cd069b070d7918b78baa
ux-motion   HEAD  67ff3f0c4912b70b7056f8226a6f226b6fe93f60
cek-runtime HEAD  f3844487d85153eecd9bb417df0293fa82ece07a
```

`gh api …/ux-dom/compare/2e894cd…d107209`:

```text
ahead_by: 1
commits: ["plan: extract-by-id public API (C2 owner gap, PLAN-ONLY) (#19)"]
files: docs/INDEX.md (3+ / 1-), docs/plans/2026-09-12-extract-by-id.md (added)
```

PyPI `cek-host` / `cek-surface` latest **0.1.3** (releases
`0.1.0`, `0.1.2`, `0.1.3`).

Product extract already shipped on the **pin**:
`ux_dom.response.serialize.__all__` includes `extract_by_id`.
Compose #83 USE is the consumer.

### 2.3 Transitive (declared, not lockfile-resolved)

```text
ux-compose @ fb7a125
├── ux-dom @ 2e894cd
│   ├── Jinja2, valio (OUT OF SCOPE), marko, anyio, typer
│   └── [optional] fastapi, uvicorn, pytailwindcss, watchfiles
├── ux-behavior @ 793f120          (zero hard deps)
├── ux-motion @ 67ff3f0            (zero hard deps)
├── ux-channel @ d0412c6
│   ├── itsdangerous
│   ├── cek-host >=0.1.3
│   └── cek-surface >=0.1.3 → cek-host
│   peer: ux-dom (glue / Soft 1+4 prefer; not a hard dep)
│   KEEP: ux_channel_ux_dom glue; asgi.mount_channel
├── cek-host>=0.1.3
└── cek-surface>=0.1.3             (declared; Isolation forbids product import)
compose extras: [serve] uvicorn watchfiles httpx starlette websockets
                [dev]   pytest* + fastapi + serve stack
                [dom]/[behavior]/[motion]/[channel]/[full] = []  (no-op aliases)
```

No compose `poetry.lock` / `uv.lock` / root `requirements.txt`. That
absence is policy. CVEs unverifiable. Do not invent lockfiles.
`cek-surface` is **used by channel / cek-runtime**, not imported in
this tree (`wire/cek.py` Isolation comment; `import cek_host` only
at `wire/cek.py:79`). Not dead — not a Soft.

Floor split: product **≥3.14**; channel / behavior / motion / cek still
advertise 3.10. Not a compose Soft.

---

## 3. Feature inventory — CLAIMED / EXPORTED / IMPLEMENTED / LOCKED

One taught path per happy path. Line numbers are compose @ `fb7a125`
unless marked channel @ `d0412c6`.

Legend: **C** claimed in docs / `__all__` / CLI · **E** on root
`__all__` or a named public door · **I** implemented · **L** a test
that would fail if the path moved.

### 3.1 Happy paths

| # | Happy path | C | E | I | L | Verdict |
|---|------------|---|---|---|---|---------|
| C1 | `render()` tree → HTML | OWNERSHIP / AGENTS | `Component` | `helpers._serialize_tree` `:133-139`; DirectoryASGI `routing/asgi.py:101-103` | `test_source_locks.py:118`; `test_html_morph.py`; `test_host.py:386-395` | **KEEP** USE `to_html_bytes` |
| C2 | Extract `#id` from serialized HTML | AGENTS `:82`; ADR 0004 `:47-49` | internal `_fragment_for_target` (not `__all__`) | Prefer `_owner_extract_by_id` `helpers.py:26-38` → `serialize.extract_by_id` then `response.extract_by_id`; call `:275-277`. Walker escape `_element_end` / `_open_tag_id` / `:265-299` | `test_fragment_extract_owner.py`; `test_source_locks.py:108-142` | **KEEP** USE + escape. No `fragment.py` |
| C3 | Offline MorphState / `@action` | `__all__` | `MorphState`, `RefState`, `action` | `component.py:20-24`; `App.use_behavior` `app.py:81-92` `Behavior.boot` | `test_html_morph.py`; `test_offline.py`; `test_control_cap_mint.py` | **KEEP** |
| C4 | Product scaffold | `cli.py:32-33` | argv only | `scaffold.py` | `test_scaffold_create_app.py`; `test_cto_scaffold_hello_fragment.py` | **KEEP**. Homonym `uxchannel create-app` leftover-taught |
| C5 | Clock A page GET | host spec / ADR 0002 | `build` | `build.py:115+` → `routing/fastapi.py` | `test_host.py`; `test_hard_cut_ownership.py:101-110` | **KEEP** product door. Park atelier `HTMLResponse` |
| C6 | Payload → media type | host spec § | — | `_as_http_response` `routing/fastapi.py:118-125`; owner adapters `:88` / `:105` | `test_host.py` payload / fail-closed `StreamingRoute` | **DEAD** leftovers. **KEEP** teaching |
| C7 | Live Intent / Cap | Isolation docs | `App.use_channel` | `app.py:105-143` → `wire/boot.attach_channel` → `Channel.boot` `:136-138` | `test_live_cap.py`; `test_cto_cap_mint_fail_closed.py`; `test_cek_door.py` | **KEEP**. Frozen wire: `Channel`, `ChannelConfig`, `apply_host_adapter`, `Intent` |
| C8 | Cap HTTP `/action` | plan C8; channel owns | — (no compose remount) | origin forwards `/ux-channel*` `serve_dev.py:57` | `test_fragment_extract_owner.py` (`mount_channel(` absent in boot); `test_serve_dev.py` | **KEEP** owner door. Do not gut `asgi/fastapi.py` |
| C9 | Morph fragment (no shell/brand) | fragment-law docs | `update_with` | `helpers.py:386+` + `_fragment_for_target` | `test_cto_fragment_law.py`; `test_chrome.py:156` | **KEEP** USE + escape; authors write fragments |
| C10 | Motion enter / play | `__all__` `scene`/`fade`/`rise`/`slide` | same + `optional_*` | `author.py:14,23-37`; `app.use_motion` `app.py:145-153` → `wire/boot.attach_motion` `:160-166` | `test_morph_then_play.py`; `test_host.py:355-364` | **KEEP**. Channel must not learn motion |
| C11 | `serve dev` three clocks | `cli.py:15-18`; ADR 0005 | — | `cli.py` argv; `serve_dev.py` spawn; `hmr.py` WS; `tailwind.start_tailwind_watch` | `test_serve_dev.py`; `test_hmr.py`; `test_hard_cut_ownership.py:32-36` | **KEEP**. Clocks not collapsed |
| C12 | Session bag | ADR 0006 | — | `serve_state.py` lifecycle only; `Channel.boot` opens `FileStateStore` | `test_serve_dev_shared_session.py`; `test_doctor_laws.py:188-229`; `test_serve_state.py` | **KEEP**. Redis wins. Doctor `scan_store_clone` |
| C13 | Tailwind / app CSS | `cli.py:11-13` | `WebAssets` | `tailwind.py`; `cli_build.py`; `assets.py` | `test_hard_cut_ownership.py:65-81`; `test_assets.py`; `test_cli_build.py` | **KEEP** fail-closed stubs on dom |
| C14 | Ownable kit | `cli.py:42-43` | — (`uxcompose add`) | `kit/copy.py`; `kit_construct.py` next to `Component` | `test_cli_add.py`; `test_kit_construct.py` | **KEEP**. Do not port channel `components/` |
| C15 | Doctor / isolation | `__all__` `doctor` | `doctor`, `DoctorResult` | `doctor.py`; argv `cli.py:40-41` | `test_doctor_laws.py`; `test_cold_isolation.py`; `test_hard_cut_ownership.py:84-91` | **KEEP** homonym. argv delegates to library |
| C16 | HMR morph-then-reload | ADR 0005 | — | `hmr.py` WS `/__uxcompose/hmr`; insert is middleware | `test_hmr.py`; `test_source_locks.py` no hub/watcher/`Popen` | **KEEP**. Not `Document.use` |
| C17 | Response HTML helpers | host spec | — | Clock A `routing/fastapi.py:88`, `:105` | `test_host.py` CSP/HTML GET | **KEEP**. Channel Soft 4 prefer-owner |
| C18 | Cap Host identity | AGENTS Cut C floor | `App.use_cek` (not `__all__`) | `wire/cek.py:69` `apply_host_adapter`; `:79` `import cek_host`; `:113-114` | `test_cek_door.py`; `test_build_cek.py` | **KEEP**. Isolation forbids `cek_surface` here |
| C19 | Deploy checklist | `cli.py:38-39` | — | `deploy.py` | `test_deploy.py`; `test_hard_cut_ownership.py:18-25` | **KEEP** |
| C20 | Live-client script insert | module docstring | — | Product: Document `Channel.optional()`. Leftover `live_client.py:11-13` | `test_live_client.py` (incl. `document=None` no attach) | **KEEP** Document path. Park `live_client` until tests migrate |

**OWNER-WRONG live re-impl in compose:** **none.** C2 homemade walker
is escape, not a competing serialize. Channel HTML/response/kit clones
are leftover-teach + prefer-owner on tip `d0412c6`.

### 3.2 Specialist USE sites (`path:line`)

| Specialist | Compose USE | Isolation |
|------------|-------------|-----------|
| **ux-dom** `to_html_bytes` | `helpers.py:17`; `_serialize_tree` `:133-139`; `routing/asgi.py:101` | product-legal |
| **ux-dom** `extract_by_id` | `helpers.py:31`, `:34`; call `:275-277` | product-legal |
| **ux-dom** tags / `HAS_DOM` | `dom.py:28-76` re-export; `scaffold.py:149` | product-legal |
| **ux-dom** `Document` / runtime | `build.py:91-101`; `scaffold.py:147-148`; `wire/boot.py:193,202` | product-legal |
| **ux-dom** starlette adapters | `routing/fastapi.py:88` `HTMLResponse`; `:105` `StreamingResponse` | product-legal |
| **ux-dom** `Component` / `dom_tag` | `component.py:27-28` **MRO refuse only** | not a clone |
| **ux-behavior** `Component` / `MorphState` / `RefState` / `action` | `component.py:20-24` | product-legal |
| **ux-behavior** `bind` / `notify` / `update` / `Op` | `helpers.py:15-16` | product-legal |
| **ux-behavior** `Behavior.boot` | `app.py:85`, `:92` | product-legal |
| **ux-channel** `Channel` / `ChannelConfig` | `wire/boot.py:84`; `Channel.boot` `:136-138` | **wire/ only** |
| **ux-channel** `Intent` | `wire/caps.py:208`, `:247` | **wire/ only** |
| **ux-channel** `apply_host_adapter` | `wire/cek.py:69` | **wire/ only** |
| **ux-channel** `mount_channel` | **no compose import**; origin prefix `serve_dev.py:57` | owner door |
| **ux-channel** `FileStateStore` | **no compose import**; lifecycle `serve_state.py` / `serve_dev.py:22-23` | owner store |
| **ux-motion** `scene`/`fade`/`rise`/`slide` | `__init__.py:40`; `author.py:14`; `kit/overlay.py:107` | product-legal |
| **ux-motion** `Motion` / `MotionChannel` | `wire/boot.py:166` | Isolation: only here |
| **cek-host** | `wire/cek.py:79` presence; `:114` via adapter | Isolation |
| **cek-surface** | **zero imports** | Isolation forbids |

### 3.3 Public `__all__` vs lock depth

`src/ux_compose/__init__.py:93-180` is the author surface. Locked by
`tests/unit/test_architecture_public_api.py` (REQUIRED / ADDED / HOST;
nomen-cut drops `maybe_*` / `tick`).

No unimplemented `__all__` name. Thin **export-presence** locks (not
unused, not Soft):

| Export | Why thin is OK |
|--------|----------------|
| `Surface` / `SurfaceBundle` / `SurfaceError` / `scan_surfaces` / `validate_surfaces` | Used inside `App.mount` / `mount_surfaces`. Teaching them as a second product door is leftover-forbid (`ARCHITECTURE.md:210`) |
| `optional_fade` / `optional_slide` | Re-export of ux-motion IR; examples use them. `optional_plan` has a hard-deps lock |
| `AttachNote` | Tests import `AttachNotes` / `attach_notes`; type is used |
| `__version__` | `"0.1.0"` unlocked. Not a taught happy path |
| Rare DOM tags (`circle`, `thead`, …) | Re-exports; kit/examples consume the set |

`BuildResult` is public on `build.py` only — intentional, not a root
export, not a shadow door.

`examples/_common.py` re-exports `author` + motion (ADR 0004). Not a
second public root. Locked `test_architecture_public_api.py:63-69`.

---

## 4. Table E — noise / dual doors / weak locks / dead-partial

TELOS tags: **E5** two ways to do one job · **E3** claimed / implemented,
not locked · **E13** residual that holds locked L · **E14** do not invent
surface to “clean up.”

### 4.1 E5 — residual dual doors (product KEEP; leftover-teach the other)

| Taught path (KEEP) | Other door | Close how |
|--------------------|------------|-----------|
| `build()` | Teaching `App.mount` as product path | Already leftover-teach: mount = catalog scan (`ARCHITECTURE.md:206-209`). Source lock `test_source_locks.py:75-94` (CHANGELOG + ARCHITECTURE skipped for the leftover phrase) |
| `scan_surfaces` + `DirectoryRoutes.discover` | Merge the walkers | **Forbidden** |
| `Channel.boot` via `wire/` | `ActionRegistry.from_config` compose import | Keep teaching; do not add the import |
| `mount_channel` Cap HTTP | Fat FastAPI extras in channel `asgi/fastapi.py` | Soft later; **not** one Soft to gut the file |
| `uxcompose create-app` | `uxchannel create-app` (Soft 2 leftover lab) | Honesty shipped. Do not merge CLIs |
| `uxcompose doctor` → `doctor.doctor` | `uxdom` / `uxchannel` / `uxbehavior` doctors | **KEEP** homonym. Three telsos |
| Frozen serve `dev`/`prod`/`restart-channel` | argv `development`/`production`/`restart_channel` | Already exit 2 (`test_cli_help.py:75`) |
| `from ux_compose import div` | `from ux_compose.kit import` in apps | Doctor teaching; `uxcompose add` |
| Document `Channel.optional()` | `live_client.attach_live_client` | Teach Document path; do not delete until tests migrate |
| Clock A `build()` GET | atelier `apps/*/server.py` handmade `HTMLResponse` | Parked. Not one Soft |
| `host="auto"` \| `fastapi` \| `asgi` | leftover `batteries` / `starlette` | Doctor leftover tokens; fail-closed |

No **new** dual door vs #84. Nothing here is a named lie (A8).

### 4.2 E13 — KEEP (deleting drops L)

| Residual | Why | Lock |
|----------|-----|------|
| `_fragment_for_target` walker escape | Deleting drops fragment-law when `extract_by_id` is absent | `test_fragment_extract_owner.py`; `test_source_locks.py:108-142` |
| `DirectoryASGI` | Clock A degrade when FastAPI absent | `routing/asgi.py`; `test_host.py` |
| `serve_state.py` sqlite lifecycle | Isolation: origin must not import `ux_channel` | ADR 0006; `test_serve_state.py` |
| `bind_pages` / `include_directory_router` alias | Signature lock | `test_hard_cut_ownership.py:94-98` |
| Two walkers inside `build()` | Catalog ≠ HTTP path law | `test_source_locks.py` two-walker lock |
| `mount_channel` | Owner Cap HTTP ≠ Clock A | channel leftover table + gate |
| `ux_channel_ux_dom` glue | Optional interop | channel package |
| Leftover *names* in doctor/docs | Teaching tokens | `ARCHITECTURE.md` leftover tables |
| `COMPOSE_VCS_PIN = 24a182f` | Pin-bump cannot pin itself | `test_hard_deps.py:16` |
| Channel leftover clones | Soft 1–4 leftover-teach | channel `tests/gate` @ `d0412c6` |
| Empty extras `[dom]`…`[full] = []` | `pip install -e ".[full]"` must not fail closed | `pyproject.toml:36-40` |

**E13 DO (cheap leftover fail-closed on a compose HTTP door):** **none.**

### 4.3 E3 / weak locks — not Soft

Real Isolation / Cap / fragment / Clock A / pin / leftover-teach locks
exist. The weak rows sit **next to** those locks. Tightening them is
theatre polish, not claimed-false → true+lock.

| Site | Pattern | Why not a Soft |
|------|---------|----------------|
| `tests/test_offline.py:36` | `"ux_channel" not in sys.modules or True` | ISO-2 already dropped `or True` from the real lock (`test_cold_isolation.py:12-39` AST + module keys + `scan_isolation`) |
| `tests/test_offline.py:48` | `len(ops) >= 0` | Does-not-raise leftover; dispatch is locked elsewhere |
| `tests/test_return_algebra.py:50` | `or True` on protected-dispatch | Offline shim theatre |
| `tests/test_kit_chrome.py:129` | `or True` on notify payload | Comment: payload varies; dialog close is locked `:131` |
| `tests/test_xor_helpers.py:45` | `or True` on `html=` | XOR is locked by the rest of that module |
| Feature `pytest.skip` when Channel did not boot | honest skipif | Not fail-open |
| Public API export-presence | `__all__` membership | Behavior lives on host / fragment / scaffold suites |
| Load `test_stress_dispatch.py:27-35` | 1000 bumps `< 15s` | **theatre.** No SLO claimed. Do not grow |
| Concurrency `test_parallel_dispatch.py:27-38` | crash-only | **theatre.** No ordering L claimed. Do not grow |
| Unused markers `slow` / `live` | `pyproject.toml:61-64`; zero uses | Marker drift. Do not invent suites. Absence-locking markers is hygiene, fails Pattern |
| CI no `--cov-fail-under` | TESTING.md suggests 40 | Policy suggestion, not a rotting lock |

### 4.4 Claimed-false scan (stale-doc)

| Claim | Reality @ `fb7a125` | Soft? |
|-------|---------------------|-------|
| CHANGELOG Unreleased `:17-18` “Soft USE … is a separate PR” | #83 landed; same file `:41-49` records it | **No.** Unreleased stacks sequential PR notes. Chronology, not a taught dual door. Pattern = encyclopedia-only |
| CHANGELOG `:50-52` “walker stays until ux-dom owns extract” | Owner extract @ `2e894cd`; USE @ `e65971b` | **No.** Same chronology. `test_source_locks.py:138` already forbids that phrase in **ARCHITECTURE**. CHANGELOG is skipped for leftover-speak (`:81`) |
| “`COMPOSE_VCS_PIN` tracks main tip” | Pin `24a182f`, HEAD `fb7a125` | **No.** #56 KEEP; tests lock the older SHA on purpose |
| #84 plan header “verified `e65971b`” | HEAD is `fb7a125` | **No.** Historical snapshot. Do not rewrite prior plans |
| ux-dom pin vs tip `d107209` | Docs-only +1 | **No.** Product current. YAGNI |

No stale-doc teaches a **second happy path**. Agents reading CHANGELOG
Unreleased see both the older pin-PR note and the Fixed #83 bullet.

### 4.5 Fail-open parked (characterization, not Soft)

| Site | Evidence | Why not a cut |
|------|----------|---------------|
| `_live_instance` `except Exception` | `routing/fastapi.py:62-68` | Blank GET is product behavior |
| `wire/boot._bridge` `except Exception: pass` | `boot.py:51-52` | Needs cap-bridge characterization. Not “delete every `except Exception`” |
| `_normalize_plan_ops` | `helpers.py` motion probe | `plan()` / `to_plan()` duck |
| `wire/cek.py` config replace | `:99-107` | frozen `ChannelConfig`; setattr no-op |
| `serve_dev` WS disconnect `pass` | clock body | |
| `doctor` AST parse | `doctor.py` | unreadable file → diagnostic |
| `App.boot` / `build()` attach `except Exception` | progressive attach notes | fail-loud `ImportError` when the hard-dep is missing |
| `_owner_extract_by_id` `ImportError` → `None` | `helpers.py:30-36` | walker escape (locked) |

Do not open a “remove all except Exception” Soft. That is fashion.

### 4.6 Dead / partial (teaching stays)

| Artifact | Status |
|----------|--------|
| `start_css_watcher=` live param | **DEAD** |
| serve argv synonyms | **DEAD** (exit 2) |
| `routing/adapters/` | **DEAD** |
| ghost `cli/` `serve/` `services/` `helpers/` `fragment.py` | **DEAD** (absence locked) |
| argv `create` | **DEAD** (exit 2) |
| Document-absent product path | **DEAD** |
| kit HTML-string fallbacks | **DEAD** |
| Soft 1–4 as an *open* channel queue | **DEAD** |
| C2 as an *open* owner-gap | **DEAD** (extract exists; USE landed) |
| `tests/property/` | **DEAD** (absence locked) |
| `live_client.py` | **PARTIAL** leftover; tests still lock public URL refs |
| atelier handmade `HTMLResponse` | **PARTIAL** showcase |
| empty extras | **KEEP** no-op aliases |
| unused `slow` / `live` markers | **PARTIAL** marker drift |

---

## 5. Ranked DO / KEEP / DEAD / DO NOT

### DO (Phase 2 — separate PRs, one concern + Intent Vector)

**None. Soft queue is empty.**

Rejected as DO (so the next agent does not re-open them):

| Candidate | Why not |
|-----------|---------|
| CHANGELOG “separate PR” / “until ux-dom owns extract” | Unreleased chronology. Leftover-speak already forbidden in ARCHITECTURE. Encyclopedia-only → Pattern fail |
| Drop `or True` in leftover theatre tests | Real Isolation / XOR / dispatch locks exist. Theatre polish. Do not invent a second lock layer |
| Remove unused `slow` / `live` markers + absence lock | Marker drift. Hygiene. Pattern fail |
| `wire/boot._bridge` silent pass | Still needs cap-bridge characterization. Fashion if bundled with other `except`s |
| Pin ux-dom `2e894cd` → `d107209` | Docs-only plan commit. Product extract already on the pin. YAGNI |
| `COMPOSE_VCS_PIN` `24a182f` → `fb7a125` | #56 chicken-egg. Not clarity |
| Delete homemade walker | User + #83: KEEP escape. Deleting drops fragment-law |
| Promote `extract_by_id` to a new public name | E14. Already on `serialize.__all__` + `response.__all__` |
| Channel Soft 5 (`button()` / fat FastAPI) | Leftover-teach. Gutting `asgi/fastapi.py` is not one Soft |
| Atelier `HTMLResponse` | Showcase leftover vs `build()`. Not one Soft |
| Delete `live_client.py` | Tests still lock it. Park until they migrate |
| Import `cek_surface` here | Isolation forbids it. Channel already wraps |
| Grow load / concurrency / property suites | Theatre. No fail-closed hole |
| A8 rename (`optional_*`, `algebra.py`) | Not a named lie |
| Valio pin / PEP 649 | **Out of scope** |

### KEEP

C2 USE + walker escape · `mount_channel` · `Channel.boot` via `wire/` ·
Clock A + serve-dev clocks · two walkers · FileStateStore owner ·
Redis wins · kit catalog + `kit_construct` at root · doctor library
argv · leftover teaching tables · empty extras · `HAS_DOM` · Isolation
AST · channel leftover clones (prefer-owner) · `ux_channel_ux_dom` ·
dropped `tests/property` · theatre load/concurrency (do not grow) ·
PR #67 parked · `COMPOSE_VCS_PIN` #56 lag · ux-dom pin `2e894cd` ·
CHANGELOG Unreleased chronology · leftover `or True` next to real locks ·
`live_client` until tests migrate · three doctor / two create-app
homonyms.

### DEAD (doors gone, teaching stays)

`start_css_watcher=` live param · serve synonyms · `routing/adapters/` ·
ghost `cli/` `serve/` `services/` · argv `create` · Document-absent
path · kit HTML-string fallbacks · Soft 1–4 as an *open* channel queue ·
C2 as an *open* owner-gap · OWNER-WRONG Soft queue (#84).

### DO NOT (kill list)

- Fashion restyle: `cli/` `serve/` `services/` `helpers/` `fragment.py` (PR **#67**).
- Clean Architecture / hexagonal `ports/` / feature-folder drawers.
- Sixth product (`ux-app`, compose-host, channel-http, a second kit).
- Docs-first encyclopedia / INDEX rewrite without a code cut.
- Trust-boundary cut: Isolation AST, Cap mint, Cut C empty CT, CSRF.
- Gut `asgi/fastapi.py` or delete `mount_channel`.
- Merge Clock A GET with Channel `/action` or CEK Host.
- Re-lock channel Soft 1–4 internals as compose tests.
- Invent load/chaos/property harnesses for vanity.
- Public rename (`optional_*`, `algebra.py`) — A8 unless named lie.
- E14 new public surface.
- Merge the two `create-app`s or the three `doctor`s.
- Invent poetry/uv lockfiles as a “CVE fix.”
- Port channel `components/` into compose `kit/`.
- Reopen #73 / #76 / #77 / #80 / #67 / #81.
- Rewrite #84 in place.
- Valio work.

---

## 6. Soft order

| # | Owner repo | Status | Next |
|---|------------|--------|------|
| Channel S1–S4 | **ux-channel** | shipped @ `d0412c6` | none |
| Compose C2 USE | **ux-compose** | shipped @ `e65971b` #83 | none |
| ux-dom extract | **ux-dom** | shipped @ `2e894cd` #20; tip `d107209` is the plan doc | none |
| Compose pin channel | **ux-compose** | shipped #79 | do not relaunch (#81 closed) |
| Compose self-pin | **ux-compose** | **KEEP** #56 | not a honesty PR |
| Ownership Soft DO | **ux-compose** | shipped #84 | OWNER-WRONG empty |
| **Clarity / denoise / maturity Softs** | **ux-compose** | **empty** | stop |

Framework Lock held: same products, native composition styles.
Ponytail: no Soft that only rearranges folders or greps CHANGELOG.

---

## 7. Pattern / Clarity gate (any later cut)

A DO row ships only when **both** pass. Fail either → **KEEP**.

| Test | Pass | Fail |
|------|------|------|
| **Pattern** | leftover-teach / fail-closed / pin-lockstep / prefer-owner | new folder, new public name, new product door, new test *layer* |
| **Clarity** | names the leftover; one concern; same-commit lock | encyclopedia-only, or “while we’re here” |

Ponytail on every cut: YAGNI → reuse owner → stdlib → minimum local.

**Stop / revert if:** Isolation AST red · leftover-teaching red · new
root `__all__` · `mount_channel` removed · `fragment.py` added ·
`serve/` package.

---

## Appendix. One screen

```text
COMPOSE @ fb7a125 (#84 ownership plan on tip e65971b)
  build()         Clock A product door     KEEP
  wire/           Isolation / Channel.boot KEEP
  helpers.py      prefer extract_by_id     USE
                  walker escape            KEEP
  kit/            ownable catalog          KEEP
  mount_channel   Cap HTTP (channel)       KEEP

CLARITY / DENOISE / MATURITY / LOCK STRENGTH
  E5 dual doors                            leftover-taught
  E13 residuals                            hold L — KEEP
  E3 weak locks                            theatre next to real locks
  claimed-false CHANGELOG                  chronology — KEEP
  fail-open _bridge                        parked characterization

SOFT QUEUE                                 EMPTY
PINS
  channel  d0412c6 (Soft 1–4)              pin == tip
  dom      2e894cd (extract)               product current
           tip d107209                     docs-only plan — KEEP pin
  behavior/motion                          pin == tip
  compose  24a182f vs HEAD fb7a125         KEEP #56

DO NOT
  PR #67 serve/ · sixth product · Valio
  gut mount_channel · docs-first restyle
  reopen #73/#76/#77/#80/#81
  A8 rename · E14 new surface
```
