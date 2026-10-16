"""Page routes attach through one verb: routing.fastapi.bind (via host.bind).

materialize()/mount() were compat wrappers with no callers in src, apps,
examples, or other bitplorer repos.
"""
import importlib
import inspect

import ux_compose.routing as routing


def test_no_compat_attach_verbs():
    http = importlib.import_module("ux_compose.routing.fastapi")
    for name in ("materialize", "mount"):
        assert not hasattr(routing, name), name
        assert name not in routing.__all__, name
        assert not hasattr(http, name), name


def test_no_unreachable_starlette_fallbacks():
    http = importlib.import_module("ux_compose.routing.fastapi")
    for fn in (http._as_html_response, http._as_stream_response):
        assert "except ImportError" not in inspect.getsource(fn), fn.__name__
