"""LegacyTailwindEnvError surfaces from the CLI as one line, exit 2, no traceback."""
from __future__ import annotations

import pytest

import ux_compose.cli as cli
from ux_compose.tailwind import LEGACY_ENV, LegacyTailwindEnvError

# ``build`` is an alias of ``minifycss`` and prints this on stderr before dispatch.
_BUILD_ALIAS_NOTICE = (
    "uxcompose: 'build' is now 'minifycss' (CSS minify); alias kept for one release"
)


def _legacy_error_lines(cmd: str, err: str) -> list[str]:
    """The legacy-env error is one stderr line. ``build`` prepends its alias notice."""
    lines = [ln for ln in err.splitlines() if ln.strip()]
    if cmd == "build":
        assert lines[:1] == [_BUILD_ALIAS_NOTICE]
        return lines[1:]
    return lines


@pytest.mark.parametrize("cmd", ["build", "serve"])
def test_legacy_env_is_one_line_exit_2(cmd, monkeypatch, capsys):
    old = next(iter(LEGACY_ENV))
    monkeypatch.setenv(old, "1")
    mod = __import__(f"ux_compose.cli.{cmd}", fromlist=["main"])

    def boom(_rest):
        raise LegacyTailwindEnvError(f"no longer read (removed in 0.2.0): {old}")

    monkeypatch.setattr(mod, "main", boom)
    assert cli.main([cmd]) == 2
    out, err = capsys.readouterr()
    lines = _legacy_error_lines(cmd, err)
    assert len(lines) == 1, err
    assert old in lines[0] and lines[0].startswith("uxcompose: ")
    assert "Traceback" not in err + out


@pytest.mark.parametrize("cmd", ["build", "serve"])
def test_legacy_env_real_message(cmd, monkeypatch, capsys):
    """The real _reject_legacy_env message (multi-line safe) collapses to one line."""
    import ux_compose.tailwind as tw

    old = next(iter(LEGACY_ENV))
    monkeypatch.setenv(old, "1")
    mod = __import__(f"ux_compose.cli.{cmd}", fromlist=["main"])
    monkeypatch.setattr(mod, "main", lambda _rest: tw.cache_dir())
    assert cli.main([cmd]) == 2
    out, err = capsys.readouterr()
    assert len(_legacy_error_lines(cmd, err)) == 1, err
    assert old in err and LEGACY_ENV[old] in err
    assert "Traceback" not in err + out


def test_other_errors_still_raise(monkeypatch):
    mod = __import__("ux_compose.cli.build", fromlist=["main"])

    def boom(_rest):
        raise RuntimeError("unrelated")

    monkeypatch.setattr(mod, "main", boom)
    with pytest.raises(RuntimeError, match="unrelated"):
        cli.main(["build"])
