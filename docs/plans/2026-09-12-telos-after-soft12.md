# TELOS residuals after Soft 1+2

> **PLAN-ONLY.** Law stays [OWNERSHIP.md](../OWNERSHIP.md).
> Shape stays [ARCHITECTURE.md](../ARCHITECTURE.md). Not a second SSoT.
>
> Verified 2026-09-12 vs compose `7546013` and specialist tips.

| Layer | Pin / tip | Status |
|-------|-----------|--------|
| ux-compose | `7546013` | current `main` |
| ux-channel | compose pin `985e58a` / tip `ae5a675` | Soft 1 `b0a68d8` + Soft 2 `#35` on tip. Compose pin is rotting. |
| ux-dom | `e8be99a` | tip; serialize `__all__` has no extract-by-id |
| ux-behavior | `793f120` | tip |
| ux-motion | `67ff3f0` | tip |
| cek-host / cek-surface | PyPI `0.1.3` | range; no lockfile |

`COMPOSE_VCS_PIN` `957f81f` is chicken-egg (the pin-bump *is* `7546013`), not drift.

## Remaining OWNER-WRONG / dual doors / bloat

| Class | Where | Verdict |
|-------|-------|---------|
| **P0** | compose pin `985e58a` vs channel tip `ae5a675` — `pyproject.toml:25`, `Makefile:10`, `scaffold.py:267` | Pin honesty. Soft 1+2 already on tip. Separate pin PR. |
| **P1 Soft 4** | channel `python/src/ux_channel/render/response.py:15-38` `render_content` clones `__render__` / `__html__` instead of `ux_dom.response.serialize.prepare_html_body` | Reuse owner when present. Starlette stays the container. Separate channel PR. |
| **Soft 3 (open)** | channel `python/src/ux_channel/components/base.py:6-17` (`ChannelComponent` still taught as optional kit) + `LAYERS.md` `components/` row | Teaching only. No Soft 3 agent running this turn. Do not port into compose `kit/`. |
| **E13 KEEP** | compose `src/ux_compose/helpers.py:166` `_element_end`, `:244` `_fragment_for_target` | Until ux-dom owns extract-by-id. Serialize is already `to_html_bytes` (`helpers.py:17`). No `fragment.py`. |
| **KEEP** | channel `asgi/fastapi.py:79` `mount_channel` | OWNER Cap HTTP door. Do not gut the fat FastAPI extras as one Soft. |
| **KEEP** | compose Clock A `routing/fastapi.py:88` / `:105` already uses `ux_dom.response.starlette` | Soft 4 is the *channel* clone, not this file. |
| **Parked** | `routing/fastapi.py:62-68` `_live_instance` `except Exception` | Characterization, not Soft. |
| **Parked** | `apps/pulse/server.py:48`, `apps/atelier_shop/server.py:42`, `apps/atelier_studio/server.py:41` handmade FastAPI `HTMLResponse` | Atelier leftover vs `build()`. Not one Soft. |
| **DO NOT** | PR #67 `serve/` restyle; `cli/` / `helpers/` / `fragment.py`; pydantic overlay; trust-boundary cut; sixth product | Kill list. |

## Ponytail / Pattern / Clarity

1. **YAGNI** — do not delete `mount_channel`, the fragment walker, or kit modules.
2. **Reuse owner** — Soft 4 → `ux_dom.response`; compose pin → channel tip.
3. **stdlib** — walker stays until extract exists.
4. **Minimum local** — Soft 4 keeps non-str `__html__` / uid.html fallback.

**Already done / KEEP:** Soft 1 HTML→ux-dom on channel; Soft 2 create-app honesty (lab, `#35` merged); Cap `mount_channel`.

**Soft 3** remains queued. Do not duplicate kit teaching here.

**Stop:** Isolation AST red, leftover-teaching red, new root `__all__`, or `mount_channel` removed → revert.

## Soft 4 contract (channel; this agent got 403 on push)

When a channel-write agent picks this up, one concern only:

- If `ux_dom` is importable, `render_content` / `HTMLResponse.render` call
  `ux_dom.response.serialize.prepare_html_body` for `None` / `str` / `bytes` /
  `is_html_renderable` values. `SafeHtml` is a `str` subclass → owner string
  prepare (CSP stamp).
- Non-str `__html__` / uid.html stay on the local fallback.
- Starlette remains the HTTP container. Do not subclass-swap in a way that
  drops channel-only types.
- No hard ux-dom dep. No root `__all__` add. Do not touch `asgi/fastapi.py`.
- Gate: `python/tests/gate/test_response_owner_ux_dom.py` (pattern matches
  Soft 1 `test_html_owner_ux_dom.py`).
- Leftover-teach in `CHANGELOG.md` + `LAYERS.md` render/ row + FEATURES
  leftover sentence. Do **not** expand the Soft 1/2 encyclopedia-wide lock
  unless you also update every encyclopedia file in the same change.

Local implementation existed on `cursor/soft4-response-ux-dom-d030` @
`abc5869` in this run and could not be pushed (`Permission denied to
cursor[bot]`).
