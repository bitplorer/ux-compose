# ux-compose — progressive composition root
# Full stack requires Python ≥3.14 (ux-dom).

PY314 ?= /tmp/ux314venv/bin/python
PY312 ?= /tmp/ux312venv/bin/python
VENV  ?= /tmp/ux314venv

.PHONY: test test314 test312 venv314 specialists examples doctor shop

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
	PYTHONPATH=src:. python -m pytest tests/ -q

test314:
	cd $(CURDIR) && PYTHONPATH=src:. $(PY314) -m pytest tests/ -q

test312:
	PYTHONPATH=src $(PY312) -m pytest \
	  tests/test_offline.py tests/test_offline_cart.py tests/test_doctor_laws.py \
	  tests/test_cold_isolation.py tests/test_return_algebra.py tests/test_xor_helpers.py -q

examples:
	$(PY314) examples/cart.py
	$(PY314) examples/document_boot.py
	$(PY314) examples/live_asgi.py
	$(PY314) examples/cart_document.py

doctor:
	$(PY314) -m ux_compose.cli doctor --no-fail .

shop:
	PYTHONPATH=src:. $(PY314) -m uvicorn apps.atelier_shop.server:app --host 0.0.0.0 --port 8080
