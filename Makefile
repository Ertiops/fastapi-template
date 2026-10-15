PROJECT_NAME := app
PYTHON_VERSION := 3.14
UV ?= uv
UV_RUN := $(UV) run --locked --python $(PYTHON_VERSION)
TEST_WORKERS ?= 1
TEST_PATH := tests
DEV_COMPOSE := docker compose -p fastapi-template-dev -f docker-compose.dev.yaml

.PHONY: develop clean_dev local local_down local-create-migrations local-apply-migrations test test-ci lint lint-ci ruff mypy format app help

develop: ## Install locked development dependencies without discarding the venv
	$(UV) sync --locked --python $(PYTHON_VERSION) --dev
	$(UV_RUN) pre-commit install

clean_dev: ## Explicitly delete the local venv (never a dependency of develop)
	rm -rf .venv

local: ## Start only the local PostgreSQL development service
	$(DEV_COMPOSE) up -d --wait

local_down: ## Stop the local development database without removing its volume
	$(DEV_COMPOSE) down

local-create-migrations: ## Generate an Alembic migration (manual action)
	$(UV_RUN) python -m $(PROJECT_NAME).adapters.database revision --autogenerate

local-apply-migrations: ## Apply existing database migrations
	$(UV_RUN) python -m $(PROJECT_NAME).adapters.database upgrade head

test: ## Run the full test suite with resource-safe parallelism
	$(UV_RUN) pytest -vx $(TEST_PATH) -vv -n $(TEST_WORKERS)

test-ci: ## Full test suite with coverage and JUnit results
	$(UV_RUN) coverage erase
	$(UV_RUN) coverage run -m pytest $(TEST_PATH) --junitxml=junit.xml -rs -n $(TEST_WORKERS)
	$(UV_RUN) coverage combine
	$(UV_RUN) coverage report
	$(UV_RUN) coverage xml -o coverage.xml

format: ## Format code explicitly (not part of lint-ci)
	$(UV_RUN) ruff format .
	$(UV_RUN) ruff check --fix .

ruff: ## Static lint without modifying files
	$(UV_RUN) ruff check app tests

mypy: ## Static type checking
	$(UV_RUN) mypy app

lint: format mypy ## Explicitly autoformat then typecheck

lint-ci: ruff mypy ## Non-mutating validation

app: ## Run the real aiomisc/Uvicorn entrypoint
	$(UV_RUN) python -m $(PROJECT_NAME)

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | sed 's/:.*##/ /'
