# ForgeML developer tasks.
#
# Everything here is derived from the repository: `make run` is exactly the
# `python -m forgeml` entry point, and `make migrate` is exactly the Alembic
# command an operator would run. No task hides a step you would not do by hand.
#
# `verify` is the checkpoint, and it is the one target CI runs. Every check it
# performs lives here and nowhere else -- a verification command that exists
# only in the workflow file is drift waiting to happen, so if you add a gate,
# add it here. `lint` fixes; `verify` only ever reports.

BACKEND      := backend
VENV         := $(BACKEND)/.venv
PG_CONTAINER := forgeml-pg
PG_PORT      := 55432

# Absolute, so a target can `cd` and still find it. Overridable, because CI
# installs into the runner's Python rather than building a venv: there the
# checkpoint runs as `make verify PY=python`.
PY           ?= $(CURDIR)/$(VENV)/bin/python

export FORGEML_ENVIRONMENT  ?= development
export FORGEML_DATABASE_URL ?= postgresql+psycopg://forgeml:forgeml@127.0.0.1:$(PG_PORT)/forgeml

.DEFAULT_GOAL := help
.PHONY: help setup db db-stop migrate run key test lint verify example clean

help: ## Show this help
	@grep -hE '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk -F':.*?## ' '{printf "  \033[1m%-12s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  First time:  make setup && make db && make migrate && make key && make run"

setup: ## Create the venv (Python 3.11) and install locked dependencies
	@command -v python3.11 >/dev/null 2>&1 || { echo "error: Python 3.11 is required (ADR-013). Install it, or use 'uv python install 3.11'."; exit 1; }
	python3.11 -m venv $(VENV)
	$(PY) -m pip install --quiet --upgrade pip
	$(PY) -m pip install --require-hashes -r $(BACKEND)/requirements-dev.lock
	$(PY) -m pip install --no-deps --no-build-isolation --editable $(BACKEND)
	@echo "ready. next: make db"

db: ## Start PostgreSQL 16 in Docker (ADR-009; SQLite is not supported)
	@docker start $(PG_CONTAINER) 2>/dev/null || docker run -d --name $(PG_CONTAINER) \
		-e POSTGRES_USER=forgeml -e POSTGRES_PASSWORD=forgeml -e POSTGRES_DB=forgeml \
		-p $(PG_PORT):5432 postgres:16
	@printf "waiting for postgres"
	@until docker exec $(PG_CONTAINER) pg_isready -U forgeml >/dev/null 2>&1; do printf "."; sleep 0.5; done
	@echo " ready on 127.0.0.1:$(PG_PORT)"

db-stop: ## Stop PostgreSQL
	@docker stop $(PG_CONTAINER) >/dev/null 2>&1 || true

migrate: ## Apply database migrations (required before the first run)
	cd $(BACKEND) && $(PY) -m alembic upgrade head
	@echo "schema at head"

run: ## Run the control plane on http://127.0.0.1:8000
	cd $(BACKEND) && $(PY) -m forgeml

example: ## Build examples/hello-model.forge, ready to upload
	python3 scripts/forge_pack.py examples/hello-model

key: ## Mint an API key (ADR-026: key admin is out-of-band, never over HTTP)
	@cd $(BACKEND) && $(PY) -m forgeml.identity create --name "$(or $(NAME),local-dev)"

test: ## Run the full test suite (needs 'make db')
	cd $(BACKEND) && $(PY) -m pytest -q

lint: ## Format, lint, and type-check (rewrites files; 'verify' is the check)
	cd $(BACKEND) && $(PY) -m black src tests migrations \
		&& $(PY) -m ruff check src tests migrations \
		&& $(PY) -m mypy src tests

verify: example ## The checkpoint: every gate CI runs. Green here means green there.
	cd $(BACKEND) && $(PY) -m black --check src tests migrations
	cd $(BACKEND) && $(PY) -m ruff check src tests migrations
	cd $(BACKEND) && $(PY) -m mypy src tests
	cd $(BACKEND) && $(PY) -m coverage run --branch -m pytest tests
	cd $(BACKEND) && $(PY) -m coverage report --fail-under=95
	@echo "checkpoint passed"

clean: ## Remove the local artifact store and built example packages
	rm -rf $(BACKEND)/storage examples/*.forge
