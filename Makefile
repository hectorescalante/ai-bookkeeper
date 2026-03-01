SHELL := /bin/bash
.DEFAULT_GOAL := help

FRONTEND_DIR := src/frontend
BACKEND_HOST := 127.0.0.1
BACKEND_PORT := 8000
BACKEND_CMD := uv run uvicorn backend.main:app --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)
MIGRATE_CMD := uv run alembic upgrade head
LOG_DIR := logs
DEV_LOG_PREFIX := dev
LOG_RETENTION_DAYS := 14

.PHONY: help setup migrate backend frontend tauri dev dev-web test lint format typecheck build validate

help: ## Show available commands
	@awk 'BEGIN {FS = ":.*## "; printf "\nUsage: make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_.-]+:.*## / {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Install backend/frontend dependencies
	uv sync --all-extras
	pnpm --dir $(FRONTEND_DIR) install
migrate: ## Apply database migrations
	$(MIGRATE_CMD)

backend: ## Run backend API server
	$(MIGRATE_CMD)
	$(BACKEND_CMD)

frontend: ## Run frontend web dev server
	pnpm --dir $(FRONTEND_DIR) dev

tauri: ## Run full Tauri desktop app
	pnpm --dir $(FRONTEND_DIR) tauri dev

dev: ## Run backend + Tauri app together
	@bash -c '\
		mkdir -p $(LOG_DIR); \
		LOG_FILE="$(LOG_DIR)/$(DEV_LOG_PREFIX)-$$(date +%F).log"; \
		ln -sfn "$$(basename "$$LOG_FILE")" "$(LOG_DIR)/$(DEV_LOG_PREFIX).log"; \
		find "$(LOG_DIR)" -type f -name "$(DEV_LOG_PREFIX)-*.log" -mtime +$(LOG_RETENTION_DAYS) -delete; \
		echo "[make dev] Logging to $$LOG_FILE"; \
		exec > >(tee -a "$$LOG_FILE") 2>&1; \
		$(MIGRATE_CMD); \
		$(BACKEND_CMD) & BACK_PID=$$!; \
		trap "kill $$BACK_PID" EXIT INT TERM; \
		pnpm --dir $(FRONTEND_DIR) tauri dev \
	'

dev-web: ## Run backend + frontend web dev server together
	@bash -c '$(MIGRATE_CMD); $(BACKEND_CMD) & BACK_PID=$$!; trap "kill $$BACK_PID" EXIT INT TERM; pnpm --dir $(FRONTEND_DIR) dev'

test: ## Run backend tests
	uv run pytest tests -v

lint: ## Run backend lint checks
	uv run ruff check src/backend tests

format: ## Format backend and tests
	uv run ruff format src/backend tests

typecheck: ## Run backend + frontend type checks
	uv run mypy src/backend
	pnpm --dir $(FRONTEND_DIR) exec vue-tsc --noEmit

build: ## Build frontend assets
	pnpm --dir $(FRONTEND_DIR) build

validate: ## Run lint, type checks, and tests
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) test
