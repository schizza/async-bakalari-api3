SHELL := /bin/bash
.DEFAULT_GOAL := help

# ====== Nastavení ======
VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

RUFF   := $(PYTHON) -m ruff
PYTEST := $(PYTHON) -m pytest

# Prostředí
export VIRTUAL_ENV_DISABLE_PROMPT=1
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PYTHONDONTWRITEBYTECODE=1

.PHONY: help venv install update \
        lint fmt fix test coverage ci \
        validate-local validate-all \
        run run-debug run-no-cache \
        clean distclean bump-version check-versions

help:
	@echo "Použití:"
	@echo "  make venv                                  - vytvoří .venv"
	@echo "  make install                               - nainstaluje závislosti (stable HA $(HA_VERSION))"
	@echo "  make update                                - smaže .venv a nainstaluje znovu"
	@echo "  make bump-version NEW=<minor|major|patch>  - zvýší verzi balíčku"
	@echo "  make all                                   - spustí všecny potřebné testy"
	@echo "  make lint                                  - ruff check + format check"
	@echo "  make fmt                                   - ruff format"
	@echo "  make fix                                   - ruff check --fix"
	@echo "  make test                                  - pytest (tiché -q)"
	@echo "  make coverage                              - pytest s coverage"
	@echo "  make ci                                    - lint + test"
	@echo "  make check-versions                        - zkontroluje správnost verzí"
	@echo "  make clean                                 - smaže cache (pytest/ruff/build)"
	@echo "  make distclean                             - clean + smaže .venv a .ha-core"

# ====== Venv & instalace ======
venv:
	python3 -m venv $(VENV)
	@echo "✅ Venv vytvořen v $(VENV)"

install: venv
	$(PYTHON) -m pip install --upgrade pip wheel
	$(PYTHON) -m pip install -e .
	$(PYTHON) -m pip install \
		ruff pre-commit \
		pytest pytest-asyncio pytest-cov \
		bumpversion \
		validate-pyproject packaging==24.2
update:
	@echo "🧹 Aktualizace prostředí..."
	rm -rf $(VENV)
	$(MAKE) install
	@echo "✅ Hotovo."

all: ci coverage validate-local show-version

# ====== Lint & test ======
lint:
	$(RUFF) check .
	$(RUFF) format --check .
	@set -o pipefail; \
		basedpyright --outputjson | python scripts/pretty_basedpyright.py

fmt:
	$(RUFF) format .

fix:
	$(RUFF) check --fix .

test:
	$(PYTEST) -q

coverage:
	$(PYTEST)

ci: lint coverage

validate-all: ci validate-local

# ====== Úklid ======
clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info
	@echo "🧹 Cache uklizena."

distclean: clean
	rm -rf $(VENV) $(HASSFEST_CORE_DIR)
	@echo "🧨 .venv i .ha-core smazány."

# ======= Bump verze ======

bump-version:
	@if [ -z "$(NEW)" ]; then echo "Použití: make bump-version NEW=<minor|major|part>"; exit 1; fi
	bumpversion $(NEW) --allow-dirty

show-version:
	@echo "🔍 Aktuální verze:"
	@bumpversion --dry-run --list --allow-dirty part | grep current_version | cut -d= -f2
