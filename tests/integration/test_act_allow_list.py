"""Host /act doors dispatch only public actions; capped names never fall through.

Anonymous POST of a capped action that is not in MINT/REFUSE must be refused
and must not change state, even with a Channel attached.
"""
from __future__ import annotations

import pytest

pytest.importorskip("fastapi")
from starlette.testclient import TestClient

from ux_compose import Component, action


class Vault(Component):
    id = "vault"
    wiped = False
    peeks = 0

    def render(self):
        return '<div id="vault"></div>'

    @action(caps=("vault.wipe",))
    def wipe(self):
        self.wiped = True

    @action(caps=("vault.close",))
    def close_quarter(self):
        self.wiped = True

    @action(caps=("vault.pay",))
    def checkout(self):
        self.wiped = True

    @action(caps=())
    def peek(self):
        self.peeks = int(self.peeks or 0) + 1


def _check(ux, asgi, path):
    ux.add(Vault)
    c = TestClient(asgi)
    inst = ux.behavior.get("vault")
    c.post(f"{path}/vault.wipe", data={})
    assert inst.wiped is False, "capped action ran from an anonymous POST"
    c.post(f"{path}/vault.peek", data={})
    assert inst.peeks == 1, "public action must still dispatch"


def test_studio_act_refuses_capped_fall_through():
    from apps.atelier_studio import server

    from apps.atelier_studio.server import _is_public_action  # noqa: F401  (allow-list helper)

    _check(server.UX, server.asgi, "/act")


def test_pulseboard_act_refuses_capped_fall_through():
    from apps.pulseboard.app import main
    from apps.pulseboard.server import _is_public_action, attach_doors  # noqa: F401

    ux, asgi, _ = main()
    asgi = attach_doors(asgi, ux)
    _check(ux, asgi, "/act")


def test_pulse_action_refuses_capped_fall_through():
    from apps.pulse.server import _is_public_action, build  # noqa: F401

    ux, asgi, _ = build()
    _check(ux, asgi, "/action")


def test_pulseboard_close_quarter_suffix_does_not_auto_mint():
    """Only the exact desk_close.close_quarter is host-minted, not *close_quarter."""
    from apps.pulseboard.app import main
    from apps.pulseboard.server import attach_doors

    ux, asgi, _ = main()
    asgi = attach_doors(asgi, ux)
    ux.add(Vault)
    TestClient(asgi).post("/act/vault.close_quarter", data={})
    assert ux.behavior.get("vault").wiped is False


def test_pulse_checkout_suffix_does_not_auto_mint():
    """Only the exact shop.checkout is host-minted, not *checkout."""
    from apps.pulse.server import build

    ux, asgi, _ = build()
    ux.add(Vault)
    TestClient(asgi).post("/action/vault.checkout", data={})
    assert ux.behavior.get("vault").wiped is False
