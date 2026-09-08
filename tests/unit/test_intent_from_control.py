"""intent_from_control: html-unescape sealed args for Intent POST."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from tests.intent_from_control import intent_from_control


def test_intent_from_control_unescapes_sealed_args():
    html = (
        '<button type="button" data-channel-action="toast.push" '
        'data-channel-args="{&quot;message&quot;:&quot;Saved to the table&quot;}" '
        'data-channel-cap="tok.sealed">'
        "Push note</button>"
    )
    payload = intent_from_control(html, "toast.push")
    assert payload["action"] == "toast.push"
    assert payload["cap"] == "tok.sealed"
    assert payload["args"] == {"message": "Saved to the table"}


def test_intent_from_control_missing_args_is_empty_dict():
    html = (
        '<button data-ux-action="hello.inc" data-channel-action="hello.inc" '
        'data-channel-cap="tok.inc">+1</button>'
    )
    payload = intent_from_control(html, "hello.inc")
    assert payload["cap"] == "tok.inc"
    assert payload["args"] == {}


def test_intent_from_control_attr_order_cap_before_args():
    html = (
        '<button data-channel-cap="tok.order" data-channel-action="toast.push" '
        'data-channel-args="{&quot;message&quot;:&quot;A&quot;}">x</button>'
    )
    payload = intent_from_control(html, "toast.push")
    assert payload["cap"] == "tok.order"
    assert payload["args"] == {"message": "A"}


def test_intent_from_control_missing_action_raises():
    with pytest.raises(LookupError, match="toast.push"):
        intent_from_control("<div>no control</div>", "toast.push")
