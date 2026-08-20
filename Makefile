# ux-compose — progressive composition root
# Full stack requires Python ≥3.14 (ux-dom).

PY314 ?= /tmp/ux314venv/bin/python
VENV  ?= /tmp/ux314venv

.PHONY: test test314 venv314 specialists examples doctor

venv314:
	python3.14 -m venv --without-pip $(VENV) || true
	$(VENV)/bin/python -m ensurepip --upgrade
	$(VENV)/bin/python -m pip install -U pip setuptools wheel

specialists: venv314
	$(PY314) -m pip install \
	  "ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git" \
	  "ux-motion @ git+https://github.com/bitplorer/ux-motion.git" \
	  "ux-channel @ git+https://github.com/bitplorer/ux-channel.git#subdirectory=python" \
	  "ux-dom @ git+https://github.com/bitplorer/ux-dom.git" \
	  fastapi uvicorn pytest
	$(PY314) -m pip install -e .

test:
	PYTHONPATH=src python -m pytest tests/ -q

test314:
	$(PY314) -m pytest tests/ -q

examples:
	$(PY314) examples/cart.py
	$(PY314) examples/document_boot.py
	$(PY314) examples/live_asgi.py

doctor:
	$(PY314) -m ux_compose.cli doctor --no-fail .
