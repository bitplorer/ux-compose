"""RED → green: review R1 findings on params/placeholders (REVIEW_R1.md)."""
from __future__ import annotations

import logging
import os
import time

import pytest

from ux_compose import Component, div
from ux_compose.helpers import _serialize_tree


def _text(node) -> str:
    return "".join(_serialize_tree(node).split())


class G(Component):
    id = "g"

    def render(self, title, subtitle="s"):
        return div(f"{title}|{subtitle}", id=self.id)


# P0-1: stored args are kwargs, explicit args win, no collision
def test_explicit_kw_overrides_stored_positional_or_keyword():
    assert "b|s" in _text(G(title="a").render(title="b"))


def test_explicit_positional_overrides_stored():
    assert "b|t" in _text(G(title="a", subtitle="t").render("b"))


def test_positional_ctor_args_stored():
    assert "a|t" in _text(G("a", "t").render())


# P0-2: super().render(...) is not double-merged
class Base(Component):
    id = "base"

    def render(self, *, title, items=()):
        return div(f"base:{title}:{len(list(items))}", id=self.id)


class Sub(Base):
    def render(self, *, title, extra=""):
        return super().render(title=title.upper())


class SubPassThrough(Base):
    def render(self, *, items=(), **kw):
        return super().render(items=list(items) + ["x"], **kw)


class SubNoArgs(Base):
    def render(self, *, title):
        return super().render()


def test_super_render_with_override_does_not_collide():
    assert "base:A:0" in _text(Sub(title="a", extra="e").render())


def test_super_render_passthrough_kwargs():
    assert "base:t:2" in _text(SubPassThrough(title="t", items=["i"]).render())


def test_super_render_without_args_does_not_leak_subclass_params():
    with pytest.raises(TypeError):
        SubNoArgs(title="a").render()


# P1-1: performance — signature cached per class, no per-render bind
def test_signature_is_cached_per_class(monkeypatch):
    import inspect

    G(title="warm").render()
    calls = []
    real = inspect.signature
    monkeypatch.setattr(inspect, "signature", lambda *a, **k: calls.append(a) or real(*a, **k))
    for _ in range(50):
        G(title="x").render()
    assert calls == []


def test_zero_param_component_keeps_base_init():
    class Z(Component):
        def render(self):
            return div("z")

    # zero-param classes keep ux_behavior's __init__ (no extra frame)
    assert "__init__" not in Component.__dict__ and "__init__" not in Z.__dict__
    t0 = time.perf_counter()
    for _ in range(2000):
        Z()
    assert time.perf_counter() - t0 < 0.5


# P1-2: hide mode logs once per (class, missing set); invalid mode rejected
def test_hide_logs_once_per_class_and_missing_set(caplog):
    from ux_compose.placeholder import use_placeholder_mode

    class H(Component):
        id = "h"

        def render(self, *, a, b=None):
            return div(a, id=self.id)

    with use_placeholder_mode("hide"), caplog.at_level(logging.WARNING, logger="ux_compose.placeholder"):
        for _ in range(3):
            H().render()
            H().render()
    recs = [r for r in caplog.records if r.name == "ux_compose.placeholder"]
    assert len(recs) == 1 and "H" in recs[0].getMessage() and "a" in recs[0].getMessage()


def test_invalid_env_mode_is_rejected(monkeypatch):
    from ux_compose.placeholder import placeholder_mode

    monkeypatch.setenv("UX_COMPOSE_PLACEHOLDERS", "shwo")
    with pytest.raises(ValueError):
        placeholder_mode()


def test_env_mode_is_normalised(monkeypatch):
    from ux_compose.placeholder import placeholder_mode

    monkeypatch.setenv("UX_COMPOSE_PLACEHOLDERS", " Show ")
    assert placeholder_mode() == "show"


# P1-4: framework no-arg construction — instance path keeps params (documented limit for classes)
def test_app_add_instance_keeps_params():
    from ux_compose import App

    app = App()
    g = G(title="kept")
    app.add(g)
    assert "kept|s" in "".join(g.__render__().split())


# P2: serve dev must not leak the mode into its own process env
def test_serve_dev_sets_mode_only_on_spawned_workers(monkeypatch):
    import subprocess

    from ux_compose.cli import serve_dev

    monkeypatch.delenv("UX_COMPOSE_PLACEHOLDERS", raising=False)
    seen = {}
    monkeypatch.setattr(subprocess, "Popen", lambda cmd, **kw: seen.update(kw["env"]) or object())
    serve_dev._spawn(["true"], cwd=".")
    assert seen.get("UX_COMPOSE_PLACEHOLDERS") == "show"
    assert "UX_COMPOSE_PLACEHOLDERS" not in os.environ
    src = open(serve_dev.__file__, encoding="utf-8").read()
    assert 'os.environ.setdefault("UX_COMPOSE_PLACEHOLDERS"' not in src
