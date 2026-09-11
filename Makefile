# ux-compose — hard-deps composition root
# Product floor is Python ≥3.14 with the pinned specialist stack.

PY314 ?= /tmp/ux314venv/bin/python
VENV  ?= /tmp/ux314venv

# SSOT pins (keep in lockstep with pyproject.toml / scaffold REQUIREMENTS).
UX_BEHAVIOR_SHA = 793f120e3b1388925772cd069b070d7918b78baa
UX_MOTION_SHA = 67ff3f0c4912b70b7056f8226a6f226b6fe93f60
UX_CHANNEL_SHA = 985e58aee76ca683774c4d4d58ab30a1d3b6efee
UX_DOM_SHA = e8be99a52bfecd6026c200fa1c3dc6a74f87aacb

.PHONY: test test-matrix coverage test314 venv314 specialists examples doctor shop studio pulse nook test-cto test-cto-fragment-law cek-repro-morph-shell

venv314:
	python3.14 -m venv --without-pip $(VENV) || true
	$(VENV)/bin/python -m ensurepip --upgrade
	$(VENV)/bin/python -m pip install -U pip setuptools wheel

specialists: venv314
	$(PY314) -m pip install \
	  "ux-behavior @ git+https://github.com/bitplorer/ux-behavior.git@$(UX_BEHAVIOR_SHA)" \
	  "ux-motion @ git+https://github.com/bitplorer/ux-motion.git@$(UX_MOTION_SHA)" \
	  "ux-channel @ git+https://github.com/bitplorer/ux-channel.git@$(UX_CHANNEL_SHA)#subdirectory=python" \
	  "ux-dom @ git+https://github.com/bitplorer/ux-dom.git@$(UX_DOM_SHA)" \
	  "cek-host>=0.1.3" "cek-surface>=0.1.3" \
	  fastapi uvicorn pytest pytest-cov httpx
	$(PY314) -m pip install -e ".[dev]"

test:
	PYTHONPATH=src:. python -m pytest tests/ -q

test-matrix:
	PYTHONPATH=src:. python -m pytest \
	  tests/unit tests/integration tests/regression tests/feature \
	  tests/concurrency tests/load tests/security -q

# CTO gates (scaffold fragment, Cap mint / fail-closed, fragment-law).
# Isolation: product never imports ux_channel.
test-cto:
	PYTHONPATH=src:. python -m pytest tests/feature -q

# Nested-shell / fragment-law: morph HTML for #hello must not embed outer
# brand chrome. FullShellHello stays a full-shell fixture; helpers strip.
test-cto-fragment-law:
	PYTHONPATH=src:. python -m pytest tests/feature -q -m cto_red --tb=short

# Optional sibling live repro (not a product import; do not require ux_channel).
# Clone https://github.com/bitplorer/cek-auto-suite next to this repo.
cek-repro-morph-shell:
	@test -f ../cek-auto-suite/repro_morph_shell.py || { \
	  echo "missing ../cek-auto-suite/repro_morph_shell.py"; \
	  echo "clone https://github.com/bitplorer/cek-auto-suite next to ux-compose"; \
	  exit 2; }
	python ../cek-auto-suite/repro_morph_shell.py

coverage:
	PYTHONPATH=src:. python -m pytest tests/ -q --cov=ux_compose --cov-report=term-missing

test314:
	cd $(CURDIR) && PYTHONPATH=src:. $(PY314) -m pytest tests/ -q

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
	PYTHONPATH=src:. $(PY314) -m uvicorn apps.pulse.server:app --host 0.0.0.0 --port 8080

nook:
	PYTHONPATH=src:. $(PY314) -m uvicorn apps.nook.server:app --host 0.0.0.0 --port 8080
