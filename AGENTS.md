# AI Bookkeeper — Agent Guide

## Purpose
AI Bookkeeper is a local macOS desktop app that automates invoice processing for maritime freight forwarding.
It detects invoices, extracts data with AI, groups revenue/costs per booking, and produces commission reports.

## Tech Stack
- **Frontend**: Tauri + Vue 3 + PrimeVue + Tailwind CSS
- **Backend**: Python (FastAPI REST API)
- **Database**: SQLite
- **AI**: Anthropic Claude Sonnet 4.5 API
- **Storage**: iCloud Drive for PDFs and reports

## Repo Layout
- `src/backend/`: Python backend
  - `domain/`: business logic (entities, value objects)
  - `application/`: use cases
  - `ports/`: interfaces (input/output)
  - `adapters/`: concrete implementations
  - `config/`: configuration
- `src/frontend/`: Tauri + Vue app
  - `src/`: UI components, views, stores
  - `src-tauri/`: Tauri configuration
- `tests/`: backend tests by layer
- `docs/`: product + architecture docs
- `data/`: local SQLite DB (gitignored)

## Architecture Conventions
- Hexagonal architecture (ports & adapters) with DDD.
- **Domain layer** must remain dependency-free (std lib + typing only).
- Use dependency injection between use cases and ports.
- Python line length: 100; Python 3.11+.

## Setup (Local Dev)
```bash
cp .env.development .env
uv sync --all-extras
cd src/frontend && pnpm install && cd ../..
```

## Run
**Backend API:**
```bash
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```
**Frontend (dev):**
```bash
cd src/frontend && pnpm dev
```
**Full Tauri app (dev):**
```bash
cd src/frontend && pnpm tauri dev
```

## Tests & Quality
**Backend:**
```bash
uv run pytest tests -v
uv run ruff check src/backend tests
uv run ruff format src/backend tests
uv run mypy src/backend
```
**Frontend:**
```bash
cd src/frontend && pnpm vue-tsc --noEmit
```

## Helpful Docs
- `docs/architecture.md` — technical design
- `docs/application.md` — use cases + domain model
- `docs/user-stories.md` — product scope
- `docs/extraction-prompt.md` — default AI extraction prompt
