# TELOS tip e65971b — ownership / usage Soft DO

> **PLAN-ONLY.** Projection, not law. Law stays
> [OWNERSHIP.md](../OWNERSHIP.md). Shape stays
> [ARCHITECTURE.md](../ARCHITECTURE.md). Test how-to stays
> [guides/TESTING.md](../TESTING.md).
>
> Phase 0–1 cartograph only. No product code. No fashion restyle.
> No folder taxonomy overlay. No E14 new public surface.
> Cap / `mount_channel` / `Channel.boot` KEEP. PR **#67** restyle
> parked. Valio out of scope.
>
> **Verified 2026-09-12** vs compose `origin/main` `e65971b`
> (`feat(helpers): prefer ux-dom extract_by_id (C2 Soft USE) (#83)`)
> and live specialist tips fetched the same hour.

Stale inventories **#73 / #76 / #77 / #80** and fashion **#67** are
being closed by gate. This page is a **new tip map**, not a merge of
those PRs. Do not reopen them.

---

## 0. Status one-screen

| Layer | Compose pin (SSOT) | Fresh `origin/main` | Status |
|-------|--------------------|---------------------|--------|
| **ux-compose** | tip `e65971b` | `e65971b3000ad597219783e0bdacd79bc4b25df0` | current |
| **ux-channel** | `d0412c62b5180f69e76d16c913809f6c34dee269` | **same** | pin == tip (Soft 1–4) |
| **ux-dom** | `2e894cd7bca66e1da6c2f9d42b2d1a8bb937c92c` | `d107209` (**+1 docs-only**) | product pin current |
| **ux-behavior** | `793f120e3b1388925772cd069b070d7918b78baa` | **same** | pin == tip |
| **ux-motion** | `67ff3f0c4912b70b7056f8226a6f226b6fe93f60` | **same** | pin == tip |
| **cek-host / cek-surface** | `>=0.1.3` | PyPI **0.1.3** (latest) | floor met |
| **cek-runtime** | not a compose pip pin | `f384448` | Channel decide; `wire/cek.py` only |

**Already landed (do not re-do):**

| Cut | SHA / PR | What |
|-----|----------|------|
| Channel Soft 1–4 | tip `d0412c6` #34–#37 | prefer ux-dom HTML/response; create-app lab honesty; kit leftover-teach |
| Channel pin | compose #79 | lockstep `d0412c6` |
| ux-dom `extract_by_id` | `2e894cd` ux-dom #20 | owner serialize `__all__` |
| Compose C2 Soft USE | `e65971b` #83 | `helpers._fragment_for_target` prefers owner; walker KEEP as escape |

**Soft queue after this inventory: empty.** No reuse-owner Soft remains
that is one concern, fail-closed, and not a folder rearrange.

`COMPOSE_VCS_PIN` `24a182f` vs HEAD `e65971b` is the #56 chicken-egg
(create-app cannot pin the merge SHA of the PR that bumps it). Not a
fail-closed hole. Walker still holds fragment-law on that older
compose SHA. **KEEP**, not a third honesty PR.

ux-dom tip `d107209` is **plan-only** (ux-dom #19): `docs/INDEX.md` +
`docs/plans/2026-09-12-extract-by-id.md`. Compare
`2e894cd...d107209` = `ahead_by: 1`, product files unchanged.
Pinning compose to that SHA is YAGNI. **KEEP** `2e894cd`.

---

## 1. TELOS + ponytail

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
| **Concern** | One Soft; prefer reuse-owner over rename |
| **Not** | Folder move, public rename, encyclopedia, sixth product |

---

## 2. Dep cartograph — pins vs tips (pasted evidence)

### 2.1 SSOT lockstep (compose tree @ `e65971b`)

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
ux-compose  HEAD  e65971b3000ad597219783e0bdacd79bc4b25df0
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

Product extract already shipped on the **pin**:
`ux_dom.response.serialize.__all__` includes `extract_by_id`
(`serialize.py:19-25`, def `:147`). Re-exported on
`ux_dom.response.__init__`. Compose #83 USE is the consumer.

### 2.2 Transitive (declared, not lockfile-resolved)

```text
ux-compose @ e65971b
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
```

No compose `poetry.lock` / `uv.lock` / root `requirements.txt`. That
absence is policy. CVEs unverifiable. Do not invent lockfiles.
`cek-surface` is **used by channel / cek-runtime**, not imported in
this tree (`wire/cek.py:6` Isolation comment; `import cek_host` only
at `wire/cek.py:79`). Not dead — not a Soft.

Floor split: product **≥3.14**; channel / behavior / motion / cek still
advertise 3.10. Not a compose Soft.

---

## 3. Capability × owner × USE

One taught path per happy path. **Risk** is “a sibling still clones or
teaches a second door.” Line numbers are compose @ `e65971b` unless
marked channel @ `d0412c6`.

| # | Happy path | Owner | Compose / channel USE (`path:line`) | Re-implement risk | Verdict |
|---|------------|-------|--------------------------------------|-------------------|---------|
| C1 | `render()` tree → HTML | **ux-dom** `to_html_bytes` | `helpers._serialize_tree` `helpers.py:133-139`; DirectoryASGI `routing/asgi.py:101-103` | Channel leftover `lower_html` / `button()` (Soft 1 prefer-owner) | **KEEP** USE owner |
| C2 | Extract `#id` from serialized HTML | **ux-dom** `extract_by_id` @ `2e894cd` | Prefer `helpers._owner_extract_by_id` `helpers.py:26-38` → `serialize.extract_by_id` then `response.extract_by_id`; call `helpers.py:275-277`. Walker escape `_element_end` `:187`, `_open_tag_id` `:234`, `_fragment_for_target` `:265-299` | Deleting escape drops fragment-law when symbol absent (`tests/unit/test_fragment_extract_owner.py`) | **KEEP** USE + escape. No `fragment.py` |
| C3 | Offline MorphState / `@action` | **ux-behavior** | `component.py:20-24` re-export; `App.use_behavior` `app.py:81-85` `Behavior.boot` | inherit ux-dom `Component` (blocked `:66-69`) | **KEEP** |
| C4 | Product scaffold | **ux-compose** `uxcompose create-app` | `cli.py:32-33` → `scaffold.py` | `uxchannel create-app` leftover-taught (Soft 2, channel `devtools/cli.py:739-743`) | **KEEP** homonym |
| C5 | Clock A page GET | **ux-compose** + FastAPI | `build()` `build.py:115+` → `routing/fastapi.py` | atelier handmade `HTMLResponse` (`apps/pulse/server.py:48`, shop `:42`, studio `:41`) | **KEEP** product door. Park atelier |
| C6 | Payload → media type | Clock A spec | `routing/fastapi.py:118-125` `_as_http_response`; owner adapters `:88` / `:105` `ux_dom.response.starlette` | FastAPI `default_response_class`, `StreamingRoute` (fail-closed `:235-238`) | **DEAD** leftovers. **KEEP** teaching |
| C7 | Live Intent / Cap | **ux-channel** Cap Host | `App.use_channel` `app.py:105-127` → `wire/boot.attach_channel` `:55-84` → `Channel.boot` `:136-138` | `ActionRegistry.from_config` as compose import | **KEEP**. Frozen wire: `Channel`, `ChannelConfig`, `apply_host_adapter`, `Intent` |
| C8 | Cap HTTP `/action` | **ux-channel** `mount_channel` | compose does not remount; origin forwards `/ux-channel*` (`serve_dev.py`). Channel `asgi/__init__.py` exports `from ux_channel.asgi.fastapi import mount_channel` | Gutting `asgi/fastapi.py` “to slim” | **KEEP** owner door. Fat extras ≠ the door |
| C9 | Morph fragment (no shell/brand) | owner extract + behavior Ops | `update_with` `helpers.py:386+` + `_fragment_for_target` | Full-document `render()` (CTO FullShellHello) | **KEEP** USE + escape; authors write fragments |
| C10 | Motion enter / play | **ux-motion** IR v1 | `__init__.py:40` `scene`/`fade`/`rise`/`slide`; `author.py:14` + `optional_*` `:23-37`; `app.use_motion` `app.py:145-148` → `wire/boot.attach_motion` `:160-166` | Channel `transition.*` | **KEEP**. Channel must not learn motion |
| C11 | `serve dev` three clocks | **ux-compose** ADR 0005 | `cli.py` argv; `serve_dev.py` spawn | in-process HMR hub; CSS `Popen` in `hmr.py`; `--one-process` | **KEEP**. Clocks not collapsed |
| C12 | Session bag | **ux-channel** `FileStateStore` / Redis | `serve_state.py:1-10` lifecycle only | compose-owned store class | **KEEP**. Redis wins. Doctor `scan_store_clone` |
| C13 | Tailwind / app CSS | **ux-compose** `tailwind.py` + `WebAssets` | `uxcompose build` → `cli_build.py` | ux-dom `TailwindCommand` / stub `WebAssets` | **KEEP** fail-closed stubs on dom |
| C14 | Ownable kit | **ux-compose** `kit/` + `uxcompose add` | `kit/copy.py`; `kit_construct.py` next to `Component` | channel `components/` leftover-taught (Soft 3); `from ux_compose.kit import` in apps | **KEEP**. Do not port channel kit here |
| C15 | Doctor / isolation | **ux-compose** `doctor` library | `from ux_compose import doctor` + `uxcompose doctor` `cli.py:40-41` | `uxchannel` / `uxdom` / `uxbehavior` doctors (layer-local) | **KEEP** homonym. argv delegates to library |
| C16 | HMR morph-then-reload | **ux-compose** `hmr.py` | WS `/__uxcompose/hmr` | `Document.use` HMR; ux-dom `reloader/` | **KEEP**. HTML insert is middleware |
| C17 | Response HTML helpers | **ux-dom** `ux_dom.response` | Clock A `routing/fastapi.py:88`, `:105`; channel Soft 4 `render/response.py` prefers `to_html_bytes` when present | leftover channel `render_content` fallback | **KEEP**. Soft 4 shipped |
| C18 | Cap Host identity | **cek-host** via channel | `wire/cek.py:69` `apply_host_adapter`; `:79` `import cek_host`; `:113-114` idempotent after `Channel.boot` | classic `CapService` when `cek=require` | **KEEP**. Floor `channel ≥ 985e58a` |
| C19 | Deploy checklist | **ux-compose** `deploy.py` | `uxcompose deploy` | product CLI on uxdom | **KEEP** |
| C20 | Live-client script insert | Document `Channel.optional()` | product path; leftover `live_client.py:39-46` public URL refs | synthesized HTML shell (banned in module docstring) | **KEEP** Document path. Park `live_client` until tests migrate |

**OWNER-WRONG live re-impl in compose:** **none.** C2 homemade walker
is escape, not a competing serialize. Channel HTML/response/kit clones
are leftover-teach + prefer-owner on tip `d0412c6`.

**Unused exports / dead files:** root `__all__` is locked
(`tests/unit/test_architecture_public_api.py`). Kit catalog exports
are copy-targets, not a product import path. No `cli/` / `serve/` /
`services/` / `fragment.py` / `helpers/` packages. `tests/property/`
dropped (absence locked). Unused pytest markers `slow` / `live` are
marker drift — do not invent suites.

---

## 4. Especially checked

### 4.1 Channel render / response @ `d0412c6`

| Site | Evidence | Verdict |
|------|----------|---------|
| `render/response.py` Soft 4 | Prefers `ux_dom.response.serialize.is_html_renderable` + `to_html_bytes`; leftover `__render__` / `__html__` / uid.html if absent | **KEEP** leftover-teach. Not compose Soft |
| `render/morph_ir.py` `lower_html` | Soft 1 prefer ux-dom escape when present | **KEEP** leftover |
| `render/html.py` `button()` / `form_open()` | stdlib `html.escape` string helpers; not Document serialize | leftover DX. **KEEP**. Do not port into compose |
| `components/` Soft 3 | leftover-teach: not Cap product | **KEEP**. Do not port into `kit/` |

No `_guess_target_from_html` on tip `d0412c6` (tree search). Channel
does not need a compose extract Soft.

### 4.2 HTML / DOM clones in compose

| Site | What | Verdict |
|------|------|---------|
| `helpers._serialize_tree` | `to_html_bytes` only | USE owner |
| `helpers` walker | escape if `extract_by_id` missing | **KEEP** (user + #83 lock) |
| `component.__render__` `:84-91` | delegates `_serialize_tree` | USE |
| `component.py:27-28` | imports ux-dom `Component` / `dom_tag` **only** to refuse MRO collision | not a clone |
| `dom.py` | tag re-exports | **KEEP** author surface |
| `routing/asgi.py:104` | `except Exception` fallback `str(result)` | degrade when owner missing; DirectoryASGI KEEP |

### 4.3 ASGI / FastAPI extras vs Cap `mount_channel`

| Surface | Verdict |
|---------|---------|
| `ux_channel.asgi.mount_channel` | **OWNER Cap HTTP door — KEEP.** Do not delete. |
| Fat FastAPI extras in channel `asgi/fastapi.py` (trace / static / MCP / enhance) | Dual *product* surface vs Clock A. Soft later — **not** one Soft to gut the file |
| Compose `routing/fastapi.py` | Clock A GET only. Does not remount Channel |
| `serve dev` origin → channel worker `/ux-channel*` | transport split (ADR 0005). **KEEP** |

### 4.4 create-app / doctor dual doors

| Taught path | Other door | Close how |
|-------------|------------|-----------|
| `uxcompose create-app` (`cli.py:32`, `scaffold.py`) | `uxchannel create-app` (Soft 2 leftover lab) | Honesty shipped. Do not merge CLIs |
| `uxcompose doctor` → `doctor.doctor` | `uxdom doctor` (pure-dom) / `uxchannel doctor` (Cap go/no-go) | **KEEP** homonym. Layer-local |
| `from ux_compose import doctor` | argv `uxcompose doctor` | same library. Not dual |

Three doctors are three telsos. Merging them is a sixth product.

### 4.5 Exception swallows (parked — not Soft)

| Site | Evidence | Why not a cut |
|------|----------|---------------|
| `_live_instance` | `routing/fastapi.py:62-68` | Blank GET is product behavior |
| `wire/boot._bridge` | `boot.py:51-52` | Needs cap-bridge characterization |
| `_normalize_plan_ops` | `helpers.py:375-379` | Motion `plan()` / `to_plan()` probe |
| `wire/cek.py` config replace | `:99-107` | frozen `ChannelConfig`; setattr no-op |
| `serve_dev` WS | disconnect `pass` | clock body |
| `doctor` AST parse | `doctor.py:64` | unreadable file → diagnostic |

Do not open a “remove all except Exception” Soft. That is fashion.

### 4.6 Dual doors already leftover-taught (E5 KEEP)

`build()` vs teaching `App.mount` as product · two walkers
(`scan_surfaces` ≠ `DirectoryRoutes.discover`) · `Channel.boot` vs
`ActionRegistry.from_config` compose import · frozen serve verbs vs
argv synonyms (already exit 2) · `from ux_compose import div` vs
`from ux_compose.kit import` in apps · Document `Channel.optional()`
vs `live_client.attach_live_client`.

---

## 5. Ranked DO / KEEP / DEAD / DO NOT

### DO (Phase 2 — separate PRs, one concern + Intent Vector)

**None.** Soft queue is empty.

Rejected as DO (so the next agent does not re-open them):

| Candidate | Why not |
|-----------|---------|
| Pin ux-dom `2e894cd` → `d107209` | Docs-only plan commit. Product extract already on the pin. YAGNI |
| `COMPOSE_VCS_PIN` `24a182f` → `e65971b` | #56 chicken-egg. Not reuse-owner. Walker still holds L |
| Delete homemade walker | User + #83: KEEP escape. Deleting drops fragment-law |
| Promote `extract_by_id` to a new public name | E14. Already on `serialize.__all__` + `response.__all__` |
| Channel Soft 5 (`button()` / fat FastAPI) | Leftover-teach. Gutting `asgi/fastapi.py` is not one Soft |
| Atelier `HTMLResponse` | Showcase leftover vs `build()`. Not one Soft |
| Import `cek_surface` here | Isolation forbids it. Channel already wraps |
| Valio pin / PEP 649 | **Out of scope** |

### KEEP

C2 USE + walker escape · `mount_channel` · `Channel.boot` via `wire/` ·
Clock A + serve-dev clocks · two walkers · FileStateStore owner ·
Redis wins · kit catalog + `kit_construct` at root · doctor library
argv · leftover teaching tables · empty extras · `HAS_DOM` · Isolation
AST · channel leftover clones (prefer-owner) · `ux_channel_ux_dom` ·
dropped `tests/property` · theatre load/concurrency (do not grow) ·
PR #67 parked · `COMPOSE_VCS_PIN` #56 lag · ux-dom pin `2e894cd`.

### DEAD (doors gone, teaching stays)

`start_css_watcher=` live param · serve synonyms · `routing/adapters/` ·
ghost `cli/` `serve/` `services/` · argv `create` · Document-absent
path · kit HTML-string fallbacks · Soft 1–4 as an *open* channel queue ·
C2 as an *open* owner-gap (extract exists; USE landed).

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
- Public rename (`optional_*`, `algebra.py`).
- Merge the two `create-app`s or the three `doctor`s.
- Invent poetry/uv lockfiles as a “CVE fix.”
- Port channel `components/` into compose `kit/`.
- Reopen #73 / #76 / #77 / #80 / #67 / #81.
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
| **Open Softs** | — | **empty** | stop |

Framework Lock held: same products, native composition styles.
Ponytail: no Soft that only rearranges folders.

---

## 7. Pattern / Clarity gate (any later cut)

A DO row ships only when **both** pass:

| Test | Pass | Fail |
|------|------|------|
| **Pattern** | Matches leftover-teach / fail-closed / pin-lockstep / prefer-owner | New folder, new public name, new product door, new test *layer* |
| **Clarity** | Names the leftover; one concern; same-commit lock | Encyclopedia-only, or “while we’re here” |

Ponytail on every cut: YAGNI → reuse owner → stdlib → minimum local.

**Stop / revert if:** Isolation AST red · leftover-teaching red · new
root `__all__` · `mount_channel` removed · `fragment.py` added ·
`serve/` package.

---

## Appendix. One screen

```text
COMPOSE @ e65971b (#83 C2 Soft USE)
  build()         Clock A product door     KEEP
  wire/           Isolation / Channel.boot KEEP
  helpers.py      prefer extract_by_id     USE
                  walker escape            KEEP
  kit/            ownable catalog          KEEP
  mount_channel   Cap HTTP (channel)       KEEP

SOFT QUEUE                                 EMPTY
PINS
  channel  d0412c6 (Soft 1–4)              pin == tip
  dom      2e894cd (extract)               product current
           tip d107209                     docs-only plan — KEEP pin
  behavior/motion                          pin == tip
  compose  24a182f vs HEAD e65971b         KEEP #56

DO NOT
  PR #67 serve/ · sixth product · Valio
  gut mount_channel · docs-first restyle
  reopen #73/#76/#77/#80/#81
```
