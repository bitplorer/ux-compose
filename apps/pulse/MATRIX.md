# Pulse feature matrix — compose → channel tree

> **Diátaxis:** reference · **App:** `apps/pulse` · **Locks:** `tests/integration/test_pulse_feature_matrix.py`  
> Pins (tip `5d8af4c` / #86): channel `a6ab159` · behavior `7d46979` · motion `bbe7d73` · dom `2e894cd`.

One live Pulse room (`GET /matrix`) plus Clock B (`POST /ux-channel/action`) exercise every specialist happy path. HTTP is the merge bar. Playwright is optional.

## How to run

From the ux-compose repo (Python ≥ 3.14, `pip install -e ".[dev,serve]"`):

```bash
# live
make pulse
# or:
PYTHONPATH=src:. uxcompose serve dev apps.pulse.server:app --host 0.0.0.0 --port 8080

# locks
PYTHONPATH=src:. python -m pytest tests/integration/test_pulse_feature_matrix.py -q
# or:
make test-pulse-matrix
```

Smoke the live process:

```bash
curl -s localhost:8080/api/health
curl -s localhost:8080/matrix | head
curl -s localhost:8080/ux-channel/health
```

## Rows

| # | Specialist | Trigger | Expected evidence | Lock |
|---|------------|---------|-------------------|------|
| 1a | **ux-dom** | `GET /` and `GET /matrix` after `build(document=, wrap=)` | `200` `text/html`; `<html>`; `id="home"` / `id="matrix"`; GET chrome `data-uxcompose-get-chrome` | `test_matrix_1_dom_build_document_html` |
| 1b | **ux-dom** | `extract_by_id` / `_fragment_for_target` on `/matrix` HTML | Owner symbol importable; helper == owner; fragment has `#matrix` + `#matrix-stage`; no `<html>` / `<title>` / GET chrome | `test_matrix_1_dom_extract_by_id_fragment_path` |
| 2a | **ux-channel** | Pulse `build()` → `App.use_channel(asgi_app=)` → `Behavior.attach` → `Channel.boot` | `behavior._wire` is Channel; FastAPI routes include `/ux-channel`; `GET /ux-channel/health` `200` with `formats` | `test_matrix_2_channel_boot_and_mount_http` |
| 2b | **ux-channel** | `POST /ux-channel/action` (owner `mount_channel` door) | Missing cap → `401`; minted `data-channel-cap` from GET `/matrix` → `200` + `ok` / `ops` | `test_matrix_2_channel_cap_path_http` |
| 3a | **ux-behavior** | `bind(self.tick_once)` + `@action` → `dispatch("matrix.tick_once")` | GET shows `data-ux-action` + `data-channel-action` + cap; first Op is `ui.dom.morph` whose patch is the `#matrix` fragment | `test_matrix_3_bind_action_verified_ops` |
| 3b | **ux-behavior** | `Behavior.attach(asgi)` owns `Channel.boot` | `_wire is app._channel`; ASGI has `include_router`; Channel does not | `test_matrix_3_behavior_attach_owns_channel_boot` |
| 4a | **ux-motion** | `matrix.play_fade` / `play_rise` / `play_slide` then HTTP fade | Ops: morph first, then `transition.play`; plan has no `html=`; HTTP Result ops start with morph | `test_matrix_4_morph_then_motion_after_result` |
| 4b | **ux-motion** | Source scan | Pulse never writes `transition.play`; compose product (outside `wire/`) never imports `ux_channel` — Channel does not learn `transition.*` | `test_matrix_4_channel_never_learns_transition_star` |
| 5 | **Isolation** | `scan_isolation` + AST | No `ux_channel` import in `apps/pulse` or `src/ux_compose` outside `wire/` | `test_matrix_5_isolation_no_ux_channel_outside_wire` |
| 6a | **Fail-closed** | `POST /ux-channel/action` `matrix.gated` | No cap → `401`; minted cap → `200` | `test_matrix_6_cap_deny_fail_closed` |
| 6b | **Fail-closed** | `POST /ux-channel/action` with empty `Content-Type` | Channel Cut C: `400` `bad_request` (empty CT is not a format) | `test_matrix_6_empty_content_type_fail_closed` |

## Laws kept

- Cap / `Channel.boot` / `mount_channel` **KEEP**. Compose does not remount Cap HTTP.
- Walker escape in `helpers._fragment_for_target` **KEEP**. No `fragment.py`.
- Pulse is the in-tree showcase (not a sixth product). `/matrix` is one more room.
- No #67 restyle. Tailwind `className` stays Pulse stone/serif.
- Framework Lock held. Python ≥ 3.14.
