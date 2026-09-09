"""serve-dev runtime. Not argv (that is ``cli.py``).

    serve.dev       origin + ui + channel (ADR 0005)
    serve.restart   one-shot SIGUSR1
    serve.state     lifecycle only (ADR 0006)

Do not re-export those modules from this package. One import path each.
Do not fold this package into ``cli.py``.
"""
