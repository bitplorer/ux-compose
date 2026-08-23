# ux-compose — progressive composition root
# Full stack requires Python ≥3.14 (ux-dom).

PY314 ?= /tmp/ux314venv/bin/python
PY312 ?= /tmp/ux312venv/bin/python
VENV  ?= /tmp/ux314venv

.PHONY: test test-matrix coverage test314 test312 venv314 specialists examples doctor shop studio pulse

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
	  fastapi uvicorn pytest pytest-cov httpx
	$(PY314) -m pip install -e ".[dev]"

test:
	PYTHONPATH=src:. python -m pytest tests/ -q

test-matrix:
	PYTHONPATH=src:. python -m pytest \
	  tests/unit tests/integration tests/regression \
	  tests/concurrency tests/load tests/property tests/security -q

coverage:
	PYTHONPATH=src:. python -m pytest tests/ -q --cov=ux_compose --cov-report=term-missing

test314:
	cd $(CURDIR) && PYTHONPATH=src:. $(PY314) -m pytest tests/ -q

test312:
	PYTHONPATH=src $(PY312) -m pytest \
	  tests/test_offline.py tests/test_offline_cart.py tests/test_doctor_laws.py \
	  tests/test_cold_isolation.py tests/test_return_algebra.py tests/test_xor_helpers.py -q

examples:
	$(PY314) examples/foundation.py
	$(PY314) examples/chrome.py
	$(PY314) examples/shell.py
	$(PY314) examples/forms.py
	$(PY314) examples/fields.py
	$(PY314) examples/lists.py
	$(PY314) examples/feeds.py
	$(PY314) examples/commerce_more.py
	$(PY314) examples/ops.py
	$(PY314) examples/live_caps.py
	$(PY314) examples/motion_xor.py
	$(PY314) examples/cart.py
	$(PY314) examples/document_boot.py
	$(PY314) examples/live_asgi.py
	$(PY314) examples/cart_document.py

doctor:
	$(PY314) -m ux_compose.cli doctor --no-fail .

shop:
	PYTHONPATH=src:. $(PY314) -m uvicorn apps.atelier_shop.server:app --host 0.0.0.0 --port 8080

studio:
	PYTHONPATH=src:. $(PY314) -m uvicorn apps.atelier_studio.server:app --host 0.0.0.0 --port 8080

pulse:
	PYTHONPATH=src:. python -m uvicorn apps.pulse.server:app --host 0.0.0.0 --port 8080
