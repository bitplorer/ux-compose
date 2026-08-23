# ux-compose Flow Map (permanent)

> **Anyone who needs to understand the system starts here.**

This document is the residual-free contract. It is intentionally short and complete.

---

## 1. Ownership Law (non-negotiable)

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Document SSoT, tag trees, pure page discovery (`DirectoryRoutes` + `RouterHooks`), thin adapters | Host choice for composition roots |
| **ux-compose** | Author experience, progressive levels, live unit injection, **host strategy selection** (Invisible) | DOM production |
| **ux-behavior** | MorphState, `@action`, Cap Law (offline) | Wire / Caps |
| **ux-channel** | Intent, Caps, signed control, ASGI peer | Product code (Isolation Law) |
| **wire/** | The *only* door that may import channel / CEK / MotionChannel | — |

---

## 2. Progressive Levels

| Level | Unlock | Door |
|-------|--------|------|
| **L0** | Static Document | ux-dom |
| **L1** | Offline interactive + MorphState + `@action` | `App.use_behavior()` / `mount` |
| **L2** | Live Caps + Intent | `App.use_channel(asgi_app=…)` → `wire/` |
| **L3** | Motion | `App.use_motion()` → `wire/` |

Progressive Superpower Contract: code written at L1 remains correct and unchanged at higher levels.

---

## 3. Page Mount Flow (Invisible Strategy)

```text
App.mount(package_dir, asgi_app=api)
  → surfaces.scan_surfaces / validate
  → Behavior.add → unit_registry (live instances)
  → surfaces_host.attach_page_router(host=…)
       preferred (auto/fastapi/starlette):
         pure DirectoryRoutes + RouterHooks(resolve_unit=live)
         + thin adapters.fastapi.mount → asgi_app.include_router
       batteries (explicit host="batteries" only):
         DirectoryRouter (never the default for compose)
```

Authors never implement adapters. Host choice stays private.

---

## 4. Channel Attachment Flow (Isolation Law)

```text
App.use_channel(asgi_app=api)
  → wire/boot.attach_channel
  → Behavior.attach(asgi) owns Channel.boot(asgi)
  → include_router lands on the real FastAPI (never on Channel)
  → bridge_actions registers @action names on Channel.registry

Product code never imports ux_channel.
```

---

## 5. Live Request Flow

```text
Browser click → signed Intent{action, args, cap}
  → Channel verifies Cap (Cap Law)
  → registry.dispatch → Behavior.dispatch(_trusted=True)
  → list[Op]
  → ops_to_wire → Result{ops}
  → Peer applies morph / toast / transition.play
```

---

## 6. Where to change what

| Want to change… | Go to |
|-----------------|-------|
| Page discovery / path law | `ux-dom` `routing/core.py` |
| Thin FastAPI materialize | `ux-dom` `routing/adapters/fastapi.py` |
| Live unit injection / host choice | `ux-compose` `surfaces_host.py` |
| Isolation doors | `ux-compose` `wire/` |
| Author progressive API | `ux-compose` `app.py` |
| Cap mint / Intent | `ux-compose` `wire/caps.py` |
| Motion plans | `ux-motion` |

---

This map is the residual-free contract. Keep it accurate.
