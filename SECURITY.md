# Security Policy

## Supported versions

| Version | Supported |
|---------|-----------|
| 0.2.x   | Yes (best-effort while pre-1.0) |
| 0.1.x   | No (unreleased; superseded by 0.2.0) |

## Threat model

Compose’s security is the union of the levels you enabled:

| Level | Specialist | Security you get |
|-------|------------|------------------|
| 0 | ux-dom | Render + CSP stamp |
| 1 | ux-behavior | Offline Cap Law / `AuthorityError` |
| 2 | ux-channel | Live Caps, signed Intent, JTI |
| 3 | ux-motion | Plan IR (host still owns HTML escaping) |

Product code must **not** import `ux_channel` outside compose `wire/`. HMR and tunnel exist only under `uxcompose serve`.

A capped action runs when the author wraps the call in `app.trust()`, or when Channel has accepted a Cap and `wire/caps.bridge_actions` calls `dispatch_verified(name, payload)` (trust for that one call). A bool supplied by the caller is not authority. Outside dev, booting the live ASGI path fails the process when attach fails (missing `UX_CHANNEL_SECRET`, a short secret, anything else it raises). Compose sets `strict_attach=True` and does not invent a secret. See [docs/reference/host.md](docs/reference/host.md) (Cap default, Attach secret).

## Reporting

GitHub Security Advisory on [bitplorer/ux-compose](https://github.com/bitplorer/ux-compose/security/advisories/new) or **bitplorer@outlook.com**. If the bug is inside a specialist, we transfer it. Do not file a public issue for unreleased details.
