# Ownership / bloat map — TELOS + ponytail

> **PLAN-ONLY.** Do not implement deletes from this page.
> Law remains [OWNERSHIP.md](../OWNERSHIP.md). Shape remains
> [ARCHITECTURE.md](../ARCHITECTURE.md). This file is a projection:
> what each layer's *telos* is, where a sibling re-implements it, and
> which focused PRs may proceed after a human says so.
>
> **Framework Lock:** same products, native composition styles. Do not
> replace FastAPI/Starlette/ux-dom with a homemade framework, a pydantic
> overlay, or a hexagonal restyle. Callers **USE** the owner.

**Verified (this write, 2026-09-11):**

| Repo | Known prior | Fresh `origin/main` | Match |
|------|-------------|---------------------|-------|
| ux-compose | `7546013` | `7546013bad9847b8ce3a1ad2aa3019c656e9c1d4` | yes |
| ux-channel | `985e58a` | `985e58aee76ca683774c4d4d58ab30a1d3b6efee` | yes |
| ux-dom | `e8be99a` (pyproject) | `e8be99a52bfecd6026c200fa1c3dc6a74f87aacb` | yes |
| ux-behavior | `793f120` (pyproject) | `793f120e3b1388925772cd069b070d7918b78baa` | yes |
| ux-motion | `67ff3f0` (pyproject) | `67ff3f0c4912b70b7056f8226a6f226b6fe93f60` | yes |

Compose has **no** `poetry.lock` / `uv.lock` / root `requirements.txt`.
Pins are VCS SHAs in `pyproject.toml` (SSOT with `Makefile` + scaffold
`REQUIREMENTS`). Create-app `COMPOSE_VCS_PIN` is `957f81f` — one commit
behind this tip (the pin-bump *is* `7546013`). That lag is chicken-egg,
not drift. Specialist pins are **not rotting** — each SHA is the
current `origin/main` tip.

---

## Library quality gate gather (proven SHAs — folded here)

Read-only gather against the pins above. **Do not implement Soft cuts
in this PR.** Plan-only tip.

**Confirmed: DOM clone in channel.** README ownership table says
channel does **not** own HTML trees / Document (`README.md:92-97`).
The tree still implements HTML:

| Clone | Path | What it does |
|-------|------|--------------|
| `lower_html` | `ux_channel/render/morph_ir.py:162-182` | IR → HTML string (`html_lib.escape` + tag assembly). Module claims it never imports a document library (`morph_ir.py:6-7`). |
| `to_html` | `ux_channel/components/primitive.py:129-164` | Coerce values to HTML **without importing ux-dom** (`primitive.py:131`). Walks `__html__` / `__render__` / `render()`. |
| `ChannelComponent` | `ux_channel/components/base.py:34-48` | Optional channel-side UI blocks; docstring says prefer ux-dom (`base.py:6-17`). Naming avoids ux-dom `Component`. |

**ASGI nuance (do not collapse).**

| Surface | Verdict |
|---------|---------|
| `ux_channel.asgi.mount_channel` (`asgi/__init__.py:15-25`, `asgi/fastapi.py:79`) | **OWNER Cap HTTP door.** KEEP. Do **not** delete. Compose Clock A is page GET; this is Intent `/action`. Two hosts, two telsos. |
| Fat FastAPI product surface inside `asgi/fastapi.py` (~1610 LOC: trace UI, static, MCP, enhance) | Dual *product* door vs compose Clock A / `uxcompose`. Soft later — **not** by gutting this file as one concern. |
| `uxchannel create-app` (`devtools/cli.py`, `scaffold/`) | Dual product CLI vs `uxcompose create-app`. Soft (2) honesty only. |

**KEEP (quality gate — deleting drops L or invents a sixth product):**

| Keep | Why |
|------|-----|
| Cap / Isolation / compose `wire/` | Law. Cold import never pulls channel. |
| ux-dom serialize (`to_html_bytes`) | Document SSoT |
| compose `helpers._fragment_for_target` | E13 until ux-dom owns extract-by-id |
| compose Clock A + `serve-dev` clocks | ADR 0002 / 0005 |
| behavior / motion owner doors | `@action` / MorphState / `scene` — re-export, do not fork |
| `ux_channel_ux_dom` glue | Optional interop; neither core imports the other (`ux_channel_ux_dom/__init__.py:11-20`) |
| `mount_channel` Cap HTTP | Owner door (above) |

**Later Soft — one concern each, after human proceed.** Gutting
`asgi/fastapi.py` is **not** one Soft.

| Soft | Concern | Where |
|------|---------|-------|
| **S1** | HTML lower via ux-dom **when present** (`lower_html` / `to_html` call owner; stdlib escape stays if ux-dom absent) | channel `render/morph_ir.py`, `components/primitive.py` |
| **S2** | `uxchannel create-app` honesty (lab, not product path) | channel CLI help / docs |
| **S3** | Demote kit teaching (`ChannelComponent` / `components/` — already "prefer ux-dom") | channel `components/`, `LAYERS.md` |
| **S4** | `render/response.py` → reuse `ux_dom.response` when present | channel `render/response.py:1-49` |

**Kill (any Soft that does these is rejected):** fashion folder
restyle; cutting trust-boundary validation (Cap, CSRF, empty
`Content-Type` Cut C, Isolation AST); inventing a sixth product.

---

## 0. TELOS (purpose of each layer)

A layer's telos is the *end it exists to serve*. Callers import that
end. Re-implementing it elsewhere is bloat even when the clone is
"thin" or "just for DX."

| Layer | Telos (owns) | Must not own |
|-------|--------------|--------------|
| **ux-dom** | Tree → HTML (`__render__` / `to_html_bytes`), `Document` shell, package static, pure-dom `uxdom` | Product CLI, Tailwind compiler, `WebAssets`, Clock A host, HMR, Intent/Cap |
| **ux-behavior** | Product meaning → verified `list[Op]`; `MorphState` / `@action` | Raw HTML, wire codecs, Cap crypto, product serve |
| **ux-channel** | Intent → Cap → Result; wire codecs; Cap Host (cek-runtime); `StateStore`; Cap HTTP `mount_channel` | HTML trees, CSS, Document serialize, product `uxcompose serve` / Clock A |
| **ux-motion** | Presence / transition plans as data (IR v1) + reference player | `@action`, Document construction, Cap mint, product CLI |
| **cek-host** | Cap mint / verify / project (authority kernel) | HTTP Product host (Clock A), ux-dom trees |
| **cek-surface** | CEK Surface / Peer IR / carriers | ux-channel wire; a second Cap machine |
| **ux-compose** | Author composition + product CLI + Tailwind + `WebAssets` + Clock A + `wire/` door | Re-implementing any specialist above |
| **FastAPI / Starlette** | HTTP process, routing, `HTMLResponse` / JSON / WS / `StaticFiles` | Channel protocol, Document serialize |
| **uvicorn / watchfiles** | Process + reload clocks | Product verbs |

**Ponytail order** (how to shrink, never the reverse):

1. **YAGNI** — delete the unused plane if no locked L depends on it.
2. **Reuse the owner** — call the specialist / host framework.
3. **stdlib** — `html.parser`, `sqlite3`, `re` only when the owner has
   no public API yet.
4. **Minimum local** — the smallest adapter that preserves Isolation
   Law and leftover teaching.

---

## 1. Dep tree — pins + tips

### 1.1 Direct pins (compose `pyproject.toml`)

| Package | Pin kind | Pinned value | Fresh tip | Lockfile | Py floor |
|---------|----------|--------------|-----------|----------|----------|
| **ux-compose** | git (this repo) | `7546013` (`main`) | `7546013` | **none** | `>=3.14` |
| **ux-dom** | VCS SHA | `e8be99a52bfecd6026c200fa1c3dc6a74f87aacb` | same | **poetry.lock** in ux-dom | `>=3.14,<3.15` |
| **ux-channel** | VCS SHA + `#subdirectory=python` | `985e58aee76ca683774c4d4d58ab30a1d3b6efee` | same | **none** | `>=3.10,<4` |
| **ux-behavior** | VCS SHA | `793f120e3b1388925772cd069b070d7918b78baa` | same | **none** | `>=3.10` |
| **ux-motion** | VCS SHA | `67ff3f0c4912b70b7056f8226a6f226b6fe93f60` | same | **none** | `>=3.10` |
| **cek-host** | PyPI range | `>=0.1.3` | PyPI **0.1.3** = `cek-python` `cd101a7` version field | **none** | `>=3.10` |
| **cek-surface** | PyPI range | `>=0.1.3` | PyPI **0.1.3** (hard-dep `cek-host>=0.1.3`) | **none** | `>=3.10` |

`cek-runtime` (`f384448`, Rust) is **not** a compose pip pin. Channel
default decide is cek-runtime Host via `ux_channel.cek` (ADR 0009/0010).
Compose touches it only through `wire/cek.py`.

**Not in this tree (do not pull):** `ux-fnbase`, retired `ux-app`,
`cek-framework` (law repo), `harbor` (legacy shop).

### 1.2 Transitive (resolved or declared)

```text
ux-compose @ 7546013
├── ux-dom @ e8be99a
│   ├── Jinja2 >=3.1.6,<4          → lock 3.1.6
│   ├── valio >=0.1.0b6,<0.2       → lock 0.1.0b6 (PyPI latest same)
│   │   ├── typingx >=0.6,<0.7
│   │   ├── phonenumbers >=8.12.50,<9
│   │   └── pyparsing >=3.0.9,<4
│   ├── marko >=2.0,<3             → lock 2.2.3
│   ├── anyio >=4.0,<5             → lock 4.14.2
│   └── typer >=0.12,<1            → lock 0.27.1 → click
│   [optional extras, not compose hard]
│   ├── pytailwindcss, watchfiles, uvicorn, fastapi, python-multipart
│   └── fastapi lock 0.141.1 → starlette 1.6.0 + pydantic 2.13.4
├── ux-channel @ 985e58a (python/)
│   ├── itsdangerous >=2.1         → PyPI 2.2.0
│   ├── cek-host >=0.1.3
│   └── cek-surface >=0.1.3
│   [optional extras: asgi/fastapi/starlette, redis, pydantic, otel, orjson]
│   peer: ux-dom (glue tests / ux_channel_ux_dom only — not a hard dep)
├── ux-behavior @ 793f120          (zero hard deps; optional [channel])
├── ux-motion @ 67ff3f0            (zero hard deps; soft ux-dom for MotionChannel)
├── cek-host>=0.1.3                (zero hard deps)
└── cek-surface>=0.1.3             → cek-host>=0.1.3
    [optional ws: websockets>=12]

compose extras
├── [serve] uvicorn, watchfiles, httpx, starlette, websockets
│   (no fastapi — create-app REQUIREMENTS adds fastapi)
└── [dev]   pytest* + fastapi + serve stack
```

### 1.3 Pin honesty

| Fact | Path |
|------|------|
| Specialist SHAs SSOT | `pyproject.toml:24-29`, `Makefile:8-11`, `src/ux_compose/scaffold.py:267-270` |
| Create-app compose pin lags HEAD | `scaffold.py:271` `COMPOSE_VCS_PIN = 957f81f…`; tests lock it (`tests/unit/test_hard_deps.py:16`) |
| Channel pin teaching | `AGENTS.md` / `docs/OWNERSHIP.md:80` / `tests/unit/test_source_locks.py` |
| No compose lockfile | absence is policy (clone + `pip install -e ".[serve]"`), not an oversight |
| Floor split | product **3.14**; channel/behavior/motion/cek still advertise 3.10 |

---

## 2. What each dep CLAIMS / EXPORTS / IMPLEMENTS

### 2.1 ux-channel @ `985e58a` (~45k LOC Python)

**Claims.** README / `AGENTS.md`: owns Intent / Result / Cap / codecs /
peers / Cap Host / `StateStore`. Does **not** own HTML trees or CSS.
`LAYERS.md:17-18`: `asgi/` is Door F (host adapter); do not treat
FastAPI as the protocol. `LAYERS.md:22`: `components/` is optional kit
— "Product UI (use ux-dom)."

**Exports.** Root `__all__`: `Channel`, `ChannelConfig`, `create_channel`,
`ActionRegistry`, protocol types, op builders, lazy `state` / `agents` /
`audit`. CLI: `uxchannel` → `ux_channel.devtools.cli:main`. Sibling
package `ux_channel_ux_dom` (glue, not Document serialize).

**Implements (tension vs KEEP).**

| Area | Path | Verdict |
|------|------|---------|
| Cap HTTP mount | `asgi/__init__.py:15-25` → `asgi/fastapi.py:79` `mount_channel` | **KEEP** — owner Cap HTTP door. Not Clock A. Do not delete. |
| Fat FastAPI product surface (trace / static / MCP / enhance in the same ~1610-line module) | `asgi/fastapi.py` | Dual *product* door vs compose. Soft later; **not** one Soft to gut the file. |
| Starlette + pure ASGI `/action` | `asgi/starlette.py`, `asgi/core.py:38` | Cap transport adapters; keep the door |
| `lower_html` IR → HTML string | `render/morph_ir.py:162-182` | **DOM clone** (README says channel does not own HTML). Soft **S1** |
| `to_html` / `ChannelComponent` | `components/primitive.py:129-164`, `components/base.py:34-48` | **DOM clone** + optional kit. Soft **S1** + **S3** |
| `HTMLResponse` duck-type | `render/response.py:1-49` | Clone of `ux_dom.response`. Soft **S4** |
| `_guess_target_from_html` | `protocol/encode.py:151-158` | Extract guess; stays until ux-dom extract (compose walker is the product residual) |
| `uxchannel create-app` | `devtools/cli.py`, `scaffold/` | Dual product CLI. Soft **S2** honesty |
| Optional pydantic actions | `devtools/pydantic_actions.py` | Overlay — do not promote |

**Legitimate (not bloat):** `host/stores.py` `StateStore` / `FileStateStore`
/ Redis; `Channel.boot` (`host/channel.py:335`); `mount_channel`; wire
codecs; CEK adapter; client JS under `static/`; `ux_channel_ux_dom`
glue. Compose **must** use these, not clone them.

### 2.2 ux-dom @ `e8be99a`

**Claims.** Render + Document + package static + `uxdom doctor|lint|profile|add`.
Product CLI / Tailwind / `WebAssets` / DirectoryRoutes / HMR → compose
(fail-closed stubs).

**Exports.** No root `__all__`. `Document`, stub `WebAssets` /
`TailwindCommand`, tags, `Fragment`, `CreateProject` (write fail-closed),
`Channel`/`Csp`/`XElement` facades. Serialize public:
`response/serialize.py:12-18` — `to_html_bytes` / `prepare_html_*` only.
**No extract-by-id.**

**Implements (leftover, fail-closed, or still live).**

| Area | Status | Path |
|------|--------|------|
| `DirectoryRoutes` / `DirectoryASGI` / `FastAPIHost` | fail-closed | `routing/core.py:40-44`, `plugins/host/fastapi.py` |
| `DirectoryRouter` + `StreamingRoute` | **still live** (~726 LOC) | `routing/_directory_router_impl.py` |
| `plugins.hmr.HotReload` | fail-closed | `plugins/hmr/__init__.py:37-45` |
| Low-level `reloader/` WS + watchfiles | **still shipped** | `reloader/_app.py` |
| `uxdom build` | pure-dom verify (name collision) | `cli/cli.py:86-112` |
| Retired demosite | teaching tree | `demosite/` |

### 2.3 ux-behavior @ `793f120`

**Claims / exports.** Offline `Behavior`, `Component`, `MorphState`,
`@action`, chrome ops. Wire helpers (`compose` / `lower` / `attach`)
under `ux_behavior.wire` — **not** top-level `__all__`. Zero hard deps.
CLI `uxbehavior` = doctor + stubs only.

**Implements.** No Document serialize (`__render__` is
`NotImplemented` — compose supplies it). `wire/attach.py` is the
Channel ASGI attach door, not Clock A.

### 2.4 ux-motion @ `67ff3f0`

**Claims / exports.** IR v1 `scene` / recipes / `dumps`/`loads` /
`MotionChannel`. No CLI. Zero hard deps.

**Implements.** `_render.render_markup` walks `__render__` / `__html__`
at the **wire freeze** boundary (`_render.py:15-17` — "must not invent
a second stringify"). Duplicate JS: `static/` ≡ `ux_motion/scripts/`.

### 2.5 cek-host / cek-surface @ PyPI 0.1.3 (`cek-python` `cd101a7`)

**Claims.** Cap Host ≠ HTTP host. Surface must not import `ux_channel`
(D4). `cek` CLI includes `create-app` — a **parallel product path**,
orthogonal to `uxcompose create-app`.

**Implements.** No ASGI product host in the library. Demo
`ThreadingHTTPServer` only. Triple Host story: Python `Host` (product) /
`RustHostKernel` / leftover `cek-runtime/ports/cek-host-py` sketch.

### 2.6 ux-compose @ `7546013` (this repo)

**Claims.** Composition + `uxcompose` + Tailwind + `WebAssets` + Clock A
+ `wire/` only. Public `__all__`: `src/ux_compose/__init__.py:93-180`.

**Implements that look like clones (and whether they are):**

| Thing | Verdict |
|-------|---------|
| `_serialize_tree` → `to_html_bytes` | USE owner (`helpers.py:112-118`) |
| `_fragment_for_target` HTML walker | **KEEP residual** until ux-dom extract (`helpers.py:121-124`, `127-274`) |
| `DirectoryASGI` | Intentional Clock A degrade, not a peer (`routing/asgi.py:1-7`) |
| `_StaticDirASGI` ETag/Last-Modified | Compose asset law (`assets.py`) |
| `ops_to_wire` | Isolation adapter, not a codec tree (`wire/caps.py:149-184`) |
| `serve_state.clear_shared_state` sqlite `DELETE FROM kv` | Lifecycle on Channel's file; not a `FileStateStore` class (`serve_state.py:50-65`) |
| `live_client` byte-insert | Leftover vs `Document.use(..., Channel.optional())` (`live_client.py:11-13`) |

---

## 3. Capability × owning layer × re-implementing layer

| Capability | Owner | Re-implementing layer | Evidence |
|------------|-------|----------------------|----------|
| Tree → HTML serialize | **ux-dom** `to_html_bytes` | compose delegates only | `src/ux_compose/helpers.py:112-118` |
| Extract-by-id on serialized HTML | **ux-dom** (missing on serialize `__all__` @ `e8be99a`) | **compose** homemade walker | `helpers.py:121-124`, `127-274`, `360-392`; ux-dom `response/serialize.py:12-18` |
| Guess morph target from HTML | ux-dom extract (missing) | **channel** regex | `ux_channel/protocol/encode.py:151-158` |
| HTML lower / coerce (IR + kit) | **ux-dom** serialize | **channel** `lower_html` + `to_html` / `ChannelComponent` | `render/morph_ir.py:162-182`; `components/primitive.py:129-164`; `components/base.py:34-48`. README forbids HTML ownership (`README.md:92-97`). Soft **S1** / **S3** |
| Starlette `HTMLResponse` + `__render__` | **ux-dom** `response` | **channel** `render/response.py` | `render/response.py:1-49`. Soft **S4** |
| Document shell / CSP / package static | **ux-dom** | channel `render/kit.py` + `components/` string HTML | channel `LAYERS.md:16-22`; compose kit is ownable catalog |
| Intent / Cap / Result / codecs | **ux-channel** | compose `wire/` **uses** (allowed) | `wire/boot.py:84`, `wire/caps.py:208` |
| `Channel.boot` Cap door | **ux-channel** `host/channel.py:335` | leftover `ActionRegistry.from_config` as a compose door | `wire/boot.py:75-78`; `tests/unit/test_source_locks.py:474` |
| `StateStore` / File / Redis | **ux-channel** `host/stores.py` | compose must not define the class | `serve_state.py:1-11`; doctor `doctor.py:89-127` |
| Session bag clear | Channel store schema | compose `sqlite3` on shared path | `serve_state.py:50-65` |
| HTTP Product host (Clock A GET) | **compose** + **FastAPI** | ux-dom leftover `DirectoryRouter` | compose `routing/fastapi.py:1-16`; ux-dom `_directory_router_impl.py` |
| Cap HTTP `/action` mount | **channel** `ux_channel.asgi.mount_channel` | — (owner door) | `asgi/__init__.py:15-25`, `asgi/fastapi.py:79`. **KEEP.** Do not delete. |
| Fat FastAPI *product* surface next to Cap mount | **compose** Clock A + FastAPI native | channel `asgi/fastapi.py` extras (trace / MCP / enhance / static kitchen-sink) | Dual product door vs Clock A. Soft later; **not** one Soft to gut the file. |
| Cap Host (CEK) | **cek-host** via channel adapter | compose `wire/cek.py` **uses** | `wire/cek.py:1-8`, `32-69` |
| MorphState / `@action` | **ux-behavior** | compose re-exports | `component.py:20-25` |
| Motion IR | **ux-motion** | compose re-exports; motion `_render` duck-types `__render__` | `__init__.py:40`; motion `_render.py` |
| Product CLI create-app / serve / deploy | **ux-compose** `uxcompose` | **channel** `uxchannel create-app`; **cek-host** `cek create-app`; **ux-dom** retired stubs | channel `devtools/cli.py`; cek-host `cli`; ux-dom `cli/scaffold.py` |
| Tailwind compile | **compose** `tailwind.py` | ux-dom `TailwindCommand` fail-closed | `settings/commands.py` (dom) |
| App `WebAssets` | **compose** `assets.py` | ux-dom stub `WebAssets` | `settings/document.py:433-437` (dom) |
| HMR / three clocks | **compose** `hmr.py` + `serve_dev.py` | ux-dom `reloader/` + fail-closed `HotReload` | `hmr.py:1-21`; dom `reloader/` |
| UI kit widgets | **compose** `kit/` (ownable copy) | channel `components/`; leftover `from ux_compose.kit import` | `kit/__init__.py:8-9` |

---

## 4. E5 dual doors / E13 upsides / E14 forbidden

TELOS tags used here:

- **E5** — two public ways to do the same job (a second door).
- **E13** — looks extra, but holds locked L (absence lock or leftover
  teaching). Deleting drops capability.
- **E14** — do not invent new public surface to "clean up."

### 4.1 E5 — dual doors (rank: close leftover, keep product)

| Door A (KEEP) | Door B (leftover / teaching) | Close how (later PR, not this one) |
|---------------|------------------------------|------------------------------------|
| `build()` | Teaching `App.mount` as a product path | Docs/tests already: mount = catalog scan (`ARCHITECTURE.md:206-208`) |
| `scan_surfaces` + `DirectoryRoutes.discover` | Merge the walkers | **Forbidden** (`ARCHITECTURE.md:41-42`) |
| `host="auto"\|"fastapi"\|"asgi"` | `host="batteries"\|"starlette"` | Already fail-closed (`routing/host.py:50-59`) |
| FastAPI Clock A + DirectoryASGI degrade | Fold FastAPI into DirectoryASGI | **Forbidden** (`ARCHITECTURE.md:57`) |
| `Channel.boot` via `wire/boot.py` | `ActionRegistry.from_config` as compose import | Keep teaching; do not add the import (`wire/boot.py:75-78`) |
| `mount_channel` Cap HTTP (KEEP owner) | Fat FastAPI product extras in the same `asgi/fastapi.py` | Soft later; **do not delete** `mount_channel`. Gutting the file is **not** one Soft. |
| `uxcompose create-app` | `uxchannel create-app` (and `cek create-app`) | Soft **S2** honesty — lab, not product. Do not delete the CLI binary. |
| `Document.use(..., Channel.optional())` | `live_client.attach_live_client` | Teach Document path; do not delete middleware until tests migrate |
| `uxcompose serve {dev,prod,restart-channel}` | argv `development` / `production` / `restart_channel` | Already exit 2 |
| `uxcompose` product CLI | `uxdom build` name collision | ux-dom already redirects compose trees; keep fail-closed (`cli/cli.py:108-112` on dom) |
| `bind_pages=` | `include_directory_router=` | **E13** — alias locked (`test_hard_cut_ownership.py:94-98`) |
| `from ux_compose import div` | `from ux_compose.kit import X` in apps | Doctor teaching; `uxcompose add` |
| `ux_channel` root import | `ux_channel.api` (same objects) | Channel-internal E5; not compose's to close |
| `protocol.ops` vs `ux_channel.ops.Op` | name collision | Channel **E13** — tests lock them distinct |
| CEK `Host` vs `RustHostKernel` vs leftover `ports/cek-host-py` | triple Host | cek-python; compose uses Channel façade only |

### 4.2 E13 — upsides (KEEP; deleting drops L)

| Residual | Why it stays | Lock |
|----------|--------------|------|
| `_fragment_for_target` in `helpers.py` | ux-dom serialize has no extract-by-id; FullShellHello / fragment-law | `helpers.py:121-124`; `test_source_locks.py:121-135`; `CRITIC.md:35` |
| `DirectoryASGI` | Clock A degrade when FastAPI absent | `routing/asgi.py:1-7`; host spec |
| `serve_state.py` lifecycle + sqlite `DELETE` | Isolation: origin must not import `ux_channel`; Channel owns the class | ADR 0006; `serve_state.py:1-11` |
| Leftover *names* in docs/doctor | Teaching tokens (`host="batteries"`, `DirectoryRouter`, kit import) | `ARCHITECTURE.md:174-209`; doctor scans |
| `bind_pages` / `include_directory_router` alias | Signature lock | `test_hard_cut_ownership.py:94-98` |
| `COMPOSE_VCS_PIN = 957f81f` | Pin-bump commit cannot pin itself | `test_hard_deps.py:16` |
| Channel `FileStateStore` | Compose must USE it | ADR 0006 |
| ux-dom fail-closed stubs (`WebAssets`, `TailwindCommand`, `HotReload`) | Fail-loud teaching; deleting the *class* invites a silent re-add | ux-dom `test_ownership_hard_cut.py` |
| Two walkers inside `build()` | Catalog ≠ HTTP path law | `build.py:230-250`; `test_source_locks.py:450-465` |
| `ux_channel.asgi.mount_channel` | Owner Cap HTTP door (≠ Clock A) | `asgi/__init__.py:15-25`; channel layout gate imports it |
| `ux_channel_ux_dom` glue | Optional interop; neither core imports the other | `ux_channel_ux_dom/__init__.py:11-20` |

### 4.3 E14 — forbidden (do not invent)

| Do not add | Why |
|------------|-----|
| New public name on `ux_compose.__all__` to "fix" a dual door | Close the leftover door or keep teaching; do not mint a third |
| `fragment.py` / `helpers/` / `docs/MODULE_MAP.md` | `test_source_locks.py:121-157`; `ARCHITECTURE.md:93` |
| `cli/` / `serve/` / `services/` packages | Folder law (`ARCHITECTURE.md:195-201`) |
| Compose `FileStateStore` class | Isolation + ADR 0006 |
| HMR / Tailwind `Popen` inside `hmr.py` | ADR 0005 |
| Clock flags / single-uvicorn fallback | `OWNERSHIP.md:85-88` |
| Product import of `ux_channel` outside `wire/` | Isolation AST |
| Pydantic models as the author surface | Overlay; Channel already isolated this to `devtools/pydantic_actions.py` |
| Hexagonal / `ports/` / `adapters/` restyle of `routing/` | Fashion folder; Clock A pair is already the adapter |
| Sibling package (`ux-app`, `ux-compose-host`, `ux-channel-http`) | Sixth product |
| `extract_by_id` on compose `__all__` | If extract moves, it moves to **ux-dom** serialize `__all__` |
| Merging Clock A (page GET) with Channel `/action` or CEK Host | Three hosts, three telsos |
| Deleting `mount_channel` to "slim" ASGI | Owner Cap HTTP door. Fat extras ≠ the door. |

---

## 5. Ranked Soft / KEEP / DEAD

Ponytail applied. **This PR implements none of the Softs.**
**Gutting `asgi/fastapi.py` is not one Soft.**

### 5.1 Soft (one concern each, after human proceed)

Quality-gate Softs first. Older D-numbers that are *not* Soft stay
parked (extract-by-id, live_client, pin dance) until a later proceed.

| # | Action | Where | Ponytail | Not this Soft |
|---|--------|-------|----------|---------------|
| **S1** | HTML lower via ux-dom **when present**. `lower_html` / `to_html` call owner serialize / `__render__`; stdlib escape remains if ux-dom is absent (channel still has no hard ux-dom dep). | `render/morph_ir.py:162-182`, `components/primitive.py:129-164` | reuse owner | Do not add `ux_channel.extract`. Do not move compose `_fragment_for_target` in the same PR. |
| **S2** | `uxchannel create-app` honesty — teach lab / channel-only, not the product path. Point humans at `uxcompose create-app`. Keep the verb if tests lock it. | channel `devtools/cli.py`, `scaffold/`, docs | YAGNI teaching | Do not delete `uxchannel`. Do not fold into compose. |
| **S3** | Demote kit teaching. `ChannelComponent` / `components/` already say prefer ux-dom (`base.py:6-17`). Stop presenting the kit as product UI. Do not port into compose `kit/`. | channel `components/`, `LAYERS.md` | YAGNI teaching | Do not invent a sixth kit package. |
| **S4** | `render/response.py` → reuse `ux_dom.response` when present; Starlette `HTMLResponse` stays the container. | `render/response.py:1-49` | reuse owner | Do not delete Cap mount. Do not merge Clock A GET into this adapter. |

Parked (not Soft until a later proceed): ux-dom extract-by-id then
compose walker wrap; `live_client` retire; `COMPOSE_VCS_PIN` bump;
ux-dom `DirectoryRouter` after standalone tests die; motion JS
dedupe; cek `ports/cek-host-py` warning only.

### 5.2 KEEP (do not "tidy")

| Item | Reason |
|------|--------|
| Cap / Isolation / compose `wire/` | Law. Cold import never pulls channel. |
| `ux_channel.asgi.mount_channel` | Owner Cap HTTP door. Do **not** delete. |
| Fat `asgi/fastapi.py` module (until a *multi-concern* channel pass, never one Soft) | Cap mount lives here; gutting drops L |
| ux-dom serialize (`to_html_bytes`) | Document SSoT |
| compose `helpers._fragment_for_target` | E13 / fragment-law until ux-dom extract |
| compose Clock A + `serve-dev` clocks | ADR 0002 / 0005 |
| behavior / motion owner doors | Re-export only |
| `ux_channel_ux_dom` glue | Optional interop; not a Document clone |
| `Channel.boot` as the compose Cap door | Frozen import set |
| Channel-owned `FileStateStore` + compose lifecycle | ADR 0006 |
| `kit_construct.py` next to `component.py` | Copy law |
| Leftover teaching tables | Doctor + `test_source_locks.py` |
| Fail-closed stubs on ux-dom | Silent re-add is worse than a stub |
| `ops_to_wire` | Isolation projection |
| `_StaticDirASGI` ETag / Last-Modified | HMR CSS clock |
| Public `__all__` as-is | E14 |

### 5.3 DEAD (already dead; do not resurrect)

| Name | Prefer |
|------|--------|
| `ux-app` | this package |
| `cli/` `serve/` `services/` packages | verb modules |
| `HmrHub` / Tailwind `Popen` in `hmr.py` | `serve_dev` + `tailwind` |
| `Document.use` HMR | `HmrClientMiddleware` |
| `host="batteries"` / `DirectoryRouter` product path | `host="auto"` |
| `ActionRegistry.from_config` as a compose import | `Channel.boot` |
| `CapService.sign` (channel) | `mint` |
| `ux_channel.cli:main` / fashion `cli/` | `devtools.cli:main` |
| `MemoryStateStore` on channel root `__all__` | `host.stores` |
| `docs/MODULE_MAP.md` | ARCHITECTURE concern table |
| `fragment.py` | walker in `helpers.py` until ux-dom extract |
| Clock flags / one-process fallback | ADR 0005 |
| `pip install ux-compose` as the primary door | clone + `.[serve]` |

---

## 6. Kill list — what a "cleanup" PR must not do

These look like hygiene and destroy L or invent a sixth product.

| Kill | Why it is wrong here |
|------|----------------------|
| **Fashion folder restyle** (`cli/`, `helpers/`, `ports/`, `adapters/` growth, `serve/`) | Folders are import/copy laws (`ARCHITECTURE.md:80-93`). |
| **Pydantic / hexagonal overlay** | Channel already quarantines pydantic under `devtools/`. Clock A payload law is type-predicates, not models (`routing/fastapi.py:9-16`). |
| **Sibling packages / sixth product** (`ux-compose-host`, `ux-channel-http`, `ux-dom-extract`, a second kit repo) | Extract belongs **on ux-dom serialize**. Glue stays `ux_channel_ux_dom`. |
| **Docs-first** (new ontology, second ownership SSoT, `MODULE_MAP.md`) | This plan is projection. Law stays `OWNERSHIP.md`. |
| **Cutting trust-boundary validation** | Do not delete Cap verify, CSRF, empty `Content-Type` reject (channel Cut C @ `985e58a`), Isolation AST, doctor `FileStateStore` clone scan, `mount_channel`, or fail-closed missing-specialist imports to "slim" the tree. |
| **Gutting `asgi/fastapi.py` as one Soft** | Cap mount is the owner door. Fat extras are a later multi-concern pass, not S1–S4. |

---

## 7. Absence locks (do not drop L)

Any delete PR must keep these green. If a lock names leftover
*teaching*, rewrite the lock and the teaching in the **same** change —
never delete the token first.

| Lock | Protects |
|------|----------|
| `tests/regression/test_hard_cut_ownership.py` | Product CLI on `uxcompose`; HMR not Document; `WebAssets` / `DirectoryRoutes` on compose; `bind_pages` alias |
| `tests/unit/test_source_locks.py` | No `fragment.py` / `MODULE_MAP.md` / `cli/` package; two walkers; wire import freeze; leftover tables; `Channel.boot` not `ActionRegistry` |
| `tests/test_cold_isolation.py` | Cold import never loads `ux_channel` |
| `tests/unit/test_hmr.py` | No `HmrHub`; no Tailwind `Popen` in `hmr.py` |
| `tests/unit/test_cli_help.py` / `test_serve_dev.py` | Frozen serve argv; no `start_css_watcher=` |
| `tests/test_doctor_laws.py` | Product-tree `FileStateStore` clone fails |
| `tests/unit/test_hard_deps.py` | SHA lockstep + `COMPOSE_SHA = 957f81f` |
| Channel `tests/gate/test_public_api_freeze.py` | Root `__all__` freeze; no `Think` / `Component` |
| Channel `test_encyclopedia_leftover_teaching.py` | Leftover names must stay *mentioned* |
| ux-dom `tests/07_resilience/test_ownership_hard_cut.py` | No product Typer verbs; stubs fail-closed |

---

## 8. Projection plan (after human proceed)

Same products. Native composition. One concern per PR. No deletes in
the PR that only writes this map. **Softs are S1–S4 only.**

```text
human proceed
    │
    ├─ S1  channel   HTML lower via ux-dom when present
    │                 lower_html / to_html → owner; no hard ux-dom dep
    │
    ├─ S2  channel   uxchannel create-app honesty (lab, not product)
    │
    ├─ S3  channel   demote ChannelComponent / components/ kit teaching
    │
    ├─ S4  channel   render/response.py → ux_dom.response when present
    │
    └─ not Soft (do not schedule as one concern)
          gut asgi/fastapi.py
          delete mount_channel
          compose helpers walker
          live_client retire / pin dance / extract-by-id
```

**S1 contract:**

- If `ux_dom` is importable, `lower_html` / `to_html` reuse owner
  serialize / `__render__` (same duck-type order, no second stringify).
- If ux-dom is absent, keep stdlib `html.escape` (channel has no hard
  ux-dom dep — `pyproject.toml:47`).
- Do not add names to channel root `__all__`.
- Compose `_fragment_for_target` stays in `helpers.py` (E13).

**S2 contract:**

- Help / docs say product create-app is `uxcompose`.
- Do not delete `uxchannel` or fold scaffold into compose.

**S3 contract:**

- Teaching only (or extra-install). Prefer ux-dom + `ch.control`.
- Do not copy `ChannelComponent` into compose `kit/`.

**S4 contract:**

- When ux-dom is present, `render/response.py` delegates to
  `ux_dom.response` prepare/`HTMLResponse` behavior.
- Starlette/FastAPI response *container* stays the host framework.
- `mount_channel` remains the Cap HTTP door.

**Stop conditions (any PR):**

- Isolation AST red, leftover-teaching test red, new name on compose /
  channel root `__all__`, or `mount_channel` removed → revert. Do not
  "fix forward" with a sibling module or a sixth product.

---

## 9. Framework Lock (explicit)

| Product | Native style we keep |
|---------|----------------------|
| FastAPI | `APIRouter`, payload-type dispatch, no `default_response_class`, no `StreamingRoute` product path |
| Starlette | Origin proxy + optional Channel mount; not a second Clock A |
| ux-dom | Tag trees + `Document.use` + `to_html_bytes` |
| ux-channel | `Channel.boot` + `mount_channel` Cap HTTP + Intent/Result ops |
| ux-behavior | `@action` + MorphState |
| ux-motion | `scene` / recipes as data |
| cek-host | Cap Host behind `wire/cek` |

We do **not** introduce a compose-owned HTML builder, a Channel-owned
Document, a CEK-owned ASGI product host, or a pydantic author layer.

---

## 10. Confidence / gaps

Independent inventories were taken of compose, ux-channel, ux-dom,
ux-behavior, ux-motion, and cek-python at the SHAs above; key
`path:line` rows were re-read on this tip.

| Gap | Impact |
|-----|--------|
| Channel / behavior / motion / cek have **no lockfiles** — transitive extras float | Range risk, not ownership |
| `cek-runtime` Rust tree not line-audited beyond README / ports warning | Cap Host SSOT is already "via Channel adapter" |
| `ux-fnbase` exists at bitplorer but is unused | Out of scope; do not add |
| Fat extras inside `asgi/fastapi.py` beyond `mount_channel` | Not a Soft. Needs a later multi-concern channel pass if ever. |
| This page is **not** a second ownership SSoT | If it disagrees with `OWNERSHIP.md`, the law wins |

**Human proceed required** before any S1–S4 implementation PR.
This PR stays plan-only.
