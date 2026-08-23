# System Flow Map (permanent · residual-free)

> **Start here.** This is the only ownership contract.

---

## 0. One screen

```text
ux-dom      RENDER     tree → __render__ / __async_render__ → HTML str | bytes | stream
                       Document shell: control attrs, runtime script tags, CSP stamp
                       pure DirectoryRoutes + RouterHooks (discovery only)

ux-compose  DELIVERY   HTTP responses, routes on ASGI app, host strategy
            + PRODUCT  live units, progressive App, channel via wire/
            + DEV      HMR (watch + WebSocket)
            + SCAFFOLD uxcompose create-app  (sole product scaffold)

ux-behavior units, MorphState, @action (offline)
ux-channel  Intent/Caps behind wire/ only
```

**Author rule:** Render? → ux-dom. Serve / product app? → ux-compose.

---

## 1. Ownership Law (non-negotiable)

| Layer | Owns | Does **not** own |
|-------|------|------------------|
| **ux-dom** | Tag trees, `__render__` / `__async_render__`, pure body helpers, Document shell (control, runtime tags, **CSP stamp**), pure page discovery | Product HTTP delivery story, host choice, HMR process, product scaffold, channel |
| **ux-compose** | Composition root (`App`), delivery (bind routes/responses to ASGI), host strategy (Invisible), live units, **HMR (dev)**, channel via `wire/`, **sole product scaffold** | DOM tree production / serialize |
| **ux-behavior** | MorphState, `@action`, offline Cap Law | Wire / transport |
| **ux-channel** | Intent, Caps, ASGI peer | Product imports (Isolation Law) |
| **wire/** | Only door to channel / CEK / MotionChannel | — |

---

## 2. Document.use (what belongs)

| Contribution | Yes/No | Why |
|--------------|--------|-----|
| control (ChannelControl / Htmx / Null) | **Yes** | Markup dialect on the document |
| runtime script tags (XElement, …) | **Yes** | Shell scripts |
| CSP policy + **stamp** | **Yes** | Document security |
| style tags / href | **Yes** | Shell |
| HMR watch + WebSocket | **No** | Dev **delivery** → ux-compose |
| FastAPIHost / app builder | **No** | Delivery / composition → ux-compose |

---

## 3. Scaffold Law

| Command | Role |
|---------|------|
| **`uxcompose create-app`** | **Only** product application scaffold |
| `uxdom create-app` | Not the product path (do not promote) |

Industry parallel: create-next-app lives with Next, not with React.

---

## 4. Progressive Levels

| Level | Unlock | Door |
|-------|--------|------|
| **L0** | Static Document / trees | ux-dom |
| **L1** | Offline interactive + MorphState + `@action` | `App` / mount |
| **L2** | Live Caps + Intent | `App.use_channel(asgi_app=…)` → `wire/` |
| **L3** | Motion | `App.use_motion()` → `wire/` |

---

## 5. Page Mount Flow

```text
App.mount(package_dir, asgi_app=api)
  → scan surfaces → unit_registry (live)
  → pure DirectoryRoutes + RouterHooks(resolve_unit=live)
  → delivery mounts routes on api
  → page GET → tree → __async_render__ / __render__  (DOM ends)
  → compose delivery wraps HTTP on api
```

---

## 6. Channel Flow

```text
App.use_channel(asgi_app=api) → wire/ → Behavior.attach → Channel.boot
Product code never imports ux_channel.
```

---

## 7. HMR Flow (dev only)

```text
ux-compose dev edge
  watches package_dir from mount
  WebSocket on same asgi_app
  optional client stub in dev shell
Not a Document.use product API.
```

---

## 8. Where to change what

| Want to change… | Go to |
|-----------------|-------|
| Serialize / tree HTML | ux-dom dunders |
| CSP stamp / Document shell | ux-dom Document contributions |
| Path law / discovery | ux-dom `routing/core.py` |
| HTTP delivery / host bind | ux-compose delivery / `surfaces_host` |
| Live units | ux-compose |
| HMR | ux-compose (dev) |
| Product scaffold | ux-compose `scaffold.py` |
| Channel | ux-compose `wire/` |

---

## 9. Forbidden (residual generators)

- Second product `App` (`ux_dom.plugins.App.web` as recommended path)
- Product scaffold in ux-dom
- HMR as first-class Document.use
- CSP owned by FastAPI host package instead of Document
- ux-dom core importing FastAPI for serialize
- Product code importing `ux_channel`

---

Keep this file accurate. Any PR that reintroduces a dual product path fails review.
