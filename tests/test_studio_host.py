"""Studio host: host-only args never leak into @action; fragments stay stage-sized."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def test_clean_args_drops_host_keys():
    from apps.atelier_studio.server import _clean_args

    got = _clean_args(
        {
            "slug": "motion-box",
            "target": "#stage",
            "action": "motionbox.hop",
            "submit": "Hop",
            "sku": "linen",
        }
    )
    assert got == {"sku": "linen"}


def test_slug_for_action_does_not_need_referer():
    from apps.atelier_studio.server import _slug_for_action

    assert _slug_for_action("motionbox.hop") == "motion-box"
    assert _slug_for_action("share.fly") == "share"
    assert _slug_for_action("cart.add") == "shop"
    assert _slug_for_action("confirm-modal.open_modal") == "shop"


def test_urlencoded_slug_does_not_reach_action():
    from apps.atelier_studio.server import _parse_action_args

    args = _parse_action_args(
        "application/x-www-form-urlencoded",
        b"slug=motion-box&sku=oak",
    )
    assert args == {"sku": "oak"}
    assert "slug" not in args
