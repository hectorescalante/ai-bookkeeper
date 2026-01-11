# Architecture

## Overview

AI Bookkeeper is a local macOS desktop application designed to automate invoice processing for a commercial agent. The application follows **Domain-Driven Design (DDD)** principles with a **Hexagonal Architecture** (Ports and Adapters) to ensure maintainability, testability, and clear separation of concerns.

For the business domain model (entities, value objects, business rules), see [application.md](application.md).

## Technology Stack

### Backend
- **Python 3.11+** — Runtime
- **FastAPI** — REST API framework
- **uv** — Package manager (fast, modern)
- **SQLite** — Local database
- **Alembic** — Database migrations
- **pypdf** — PDF text extraction
- **openpyxl** — Excel report generation

### Frontend
- **Tauri** — Desktop shell (Rust-based)
- **Vue 3** — UI framework (Composition API)
- **PrimeVue** — Component library
- **Tailwind CSS** — Styling
- **TypeScript** — Type safety
- **pnpm** — Package manager

### AI & External Services
- **Anthropic Claude Sonnet 4.5** — Invoice data extraction (direct API)
- **Microsoft Graph API** — Outlook email access (OAuth2)

### Development & Quality
- **pytest** — Testing framework
- **ruff** — Linting and formatting
- **mypy** — Static type checking

## Architectural Principles

### Domain-Driven Design (DDD)
- **Ubiquitous Language**: Shared vocabulary between domain experts and developers
- **Single Bounded Context**: Invoice Tracking (entire app is one context)
- **Rich Domain Model**: Business logic lives in the domain layer, not in services

### Hexagonal Architecture
- **Dependency Inversion**: Domain depends on nothing; everything depends on domain
- **Ports**: Interfaces defined by the domain for external interactions
- **Adapters**: Implementations that connect ports to external systems

## Hexagonal Architecture Diagram

```
                    ┌──────────────────────┐
                    │  Tauri + Vue 3       │
                    └──────────┬───────────┘
                               │
         ┌─────────────────────▼─────────────────────┐
         │           DRIVING ADAPTERS                │
         │     HTTP API  │  CLI  │  Event Handler    │
         └─────────────────────┬─────────────────────┘
                               │
         ┌─────────────────────▼─────────────────────┐
         │              INPUT PORTS                  │
         │          (Use Case Interfaces)            │
         └─────────────────────┬─────────────────────┘
                               │
    ┌──────────────────────────▼──────────────────────────┐
    │                  APPLICATION LAYER                   │
    │              (Use Case Implementations)              │
    └──────────────────────────┬──────────────────────────┘
                               │
    ┌──────────────────────────▼──────────────────────────┐
    │                    DOMAIN LAYER                      │
    │   Entities │ Value Objects │ Services │ Events      │
    └──────────────────────────┬──────────────────────────┘
                               │
         ┌─────────────────────▼─────────────────────┐
         │              OUTPUT PORTS                 │
         │     Repositories  │  External Services    │
         └─────────────────────┬─────────────────────┘
                               │
         ┌─────────────────────▼─────────────────────┐
         │            DRIVEN ADAPTERS                │
         │  SQLite │ Anthropic │ Outlook │ iCloud    │
         │  Excel  │ Keychain                        │
         └───────────────────────────────────────────┘
```

For details on ports and domain model, see [application.md](application.md).

## Adapters

Adapters implement the ports defined in [application.md](application.md).

### Driven Adapters (Infrastructure)
Concrete implementations of output ports.

- **SQLite Adapter** — All repositories use local SQLite database (Alembic migrations)
- **Anthropic Adapter** — Claude Sonnet 4.5 API integration (direct Anthropic API)
- **Outlook Adapter** — Microsoft Graph API with OAuth2 user consent
- **iCloud Adapter** — Local filesystem in iCloud Drive folder (manual cleanup, user responsibility)
- **Excel Adapter** — Generate .xlsx files using openpyxl
- **SecretStore Adapter** — Encrypted settings file (`settings.enc`) with machine-specific key
- **PDF Adapter** — pypdf for text extraction; scanned PDFs sent as images directly to Claude

### Driving Adapters (UI/API)
How external actors interact with the application.

- **REST API** — Python backend exposes local HTTP REST API; Vue 3 frontend consumes it. Enables future SaaS migration without frontend changes.
- **CLI Handler** — Optional command-line interface
- **Event Handler** — React to domain events

## Project Structure

```
ai-bookkeeper/
├── src/
│   ├── backend/                 # Python
│   │   ├── domain/              # Pure business logic (no external dependencies)
│   │   │   ├── entities/        # Booking, invoices, Client, Provider, Company, Agent, Settings
│   │   │   ├── value_objects/   # Money, BookingCharge, Port, etc.
│   │   │   ├── services/        # InvoiceClassifier, DuplicateChecker, InvoiceValidator
│   │   │   └── events/          # Domain events
│   │   ├── application/         # Use cases (orchestration layer)
│   │   ├── ports/               # Interface definitions (input & output)
│   │   ├── adapters/            # Infrastructure implementations
│   │   └── config/              # Dependency injection
│   └── frontend/                # Tauri + Vue 3
│       ├── src/                 # Vue application
│       │   ├── components/      # Reusable UI components (PrimeVue + custom)
│       │   ├── views/           # Page components (Documents, Bookings, Settings)
│       │   ├── composables/     # Vue composables (shared logic)
│       │   ├── services/        # API calls to backend
│       │   └── types/           # TypeScript types
│       └── src-tauri/           # Rust/Tauri shell
├── tests/
└── docs/
```

## Environments

### Development
Local development with hot reload and debugging.

| Component | Configuration |
|-----------|---------------|
| **Frontend** | Vite dev server with HMR (`localhost:5173`) |
| **Backend** | Python with auto-reload (`localhost:8000`) |
| **Database** | SQLite file in project: `data/dev.db` |
| **AI API** | Real Claude API (dev key) or mock responses |
| **Outlook** | Mock email client (no real OAuth) |
| **File Storage** | Local temp folder: `data/pdfs/` |
| **Logging** | DEBUG level, console output |

```bash
# Start development
pnpm tauri dev          # Frontend + Tauri
python -m uvicorn ...   # Backend API
```

### Staging
Pre-release testing with real integrations. Distributed to beta testers.

| Component | Configuration |
|-----------|---------------|
| **App** | Signed build, not notarized |
| **Database** | SQLite in user data folder |
| **AI API** | Real Claude API (staging key) |
| **Outlook** | Real OAuth (test account) |
| **File Storage** | iCloud Drive staging folder |
| **Logging** | INFO level, file output |
| **Updates** | Manual distribution (DMG/ZIP) |

Used for:
- Testing full workflows with real APIs
- Beta user feedback
- Pre-release validation

### Production
Released application for end users.

| Component | Configuration |
|-----------|---------------|
| **App** | Signed + notarized macOS build |
| **Database** | SQLite: `~/Library/Application Support/AIBookkeeper/data.db` |
| **AI API** | User's own Anthropic API key |
| **Outlook** | Real OAuth (user's account) |
| **File Storage** | iCloud Drive: `~/Library/Mobile Documents/com~apple~CloudDocs/AIBookkeeper/` |
| **Logging** | INFO level (DEBUG disabled), file output |
| **Updates** | Auto-update via Tauri updater (future) |

### Environment Variables

```bash
# .env.development
AIBOOKKEEPER_ENV=development
AIBOOKKEEPER_LOG_LEVEL=DEBUG
AIBOOKKEEPER_DB_PATH=./data/dev.db
AIBOOKKEEPER_MOCK_OUTLOOK=true
AIBOOKKEEPER_MOCK_AI=false

# .env.staging
AIBOOKKEEPER_ENV=staging
AIBOOKKEEPER_LOG_LEVEL=INFO
AIBOOKKEEPER_MOCK_OUTLOOK=false
AIBOOKKEEPER_MOCK_AI=false

# .env.production (embedded in build)
AIBOOKKEEPER_ENV=production
AIBOOKKEEPER_LOG_LEVEL=INFO
```

---

## Testing Strategy

- **Unit Tests** — Domain layer logic in isolation (no external dependencies)
- **Integration Tests** — Adapters against real SQLite, file system
- **E2E Tests** — Full workflows through the Tauri API

### Tools & Coverage Goals
- **pytest** — Test runner
- **ruff** — Linting and formatting (replaces black, isort, flake8)
- **mypy** — Static type checking
- Coverage: Domain 90%+, Adapters 80%+, Use Cases 85%+

## Logging & Diagnostics

Robust logging for troubleshooting issues on user machines.

### Log Levels
- **ERROR** — Failures requiring attention (API errors, crashes, validation failures)
- **WARNING** — Recoverable issues (stuck documents, retry attempts)
- **INFO** — Key operations (document processed, booking updated, report generated)
- **DEBUG** — Detailed execution flow (disabled in production by default)

### Log Location
```
~/Library/Logs/AIBookkeeper/
├── app-2024-01-15.log    # One file per day
├── app-2024-01-14.log
└── app-2024-01-13.log
```

### Log Format (Structured JSON)
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "component": "ProcessInvoice",
  "message": "Invoice processed successfully",
  "context": {
    "document_id": "doc-123",
    "booking_id": "BL-2024-001234",
    "duration_ms": 2340
  }
}
```

### What to Log
- Use case start/end with duration
- External API calls (Outlook, Claude) with status codes
- Document status transitions
- Validation errors with field names
- Database operations (without data)
- User actions (process, complete, export)

### What NOT to Log (Privacy)
- API keys or tokens
- Invoice amounts or financial data
- Client/provider names or NIFs
- PDF content or extracted text
- Email subjects or senders
- Any personally identifiable information

### Log Rotation
- One file per day (`app-YYYY-MM-DD.log`)
- Retention: 30 days
- Older files auto-deleted on startup

### Export Diagnostic Bundle
User can generate a diagnostic bundle for developer support:

**Settings → Help → Export Diagnostics**

Bundle contents (`diagnostics-YYYYMMDD-HHMMSS.zip`):
- `logs/` — Last 5 log files
- `app-info.json` — App version, OS version, Python version
- `config-summary.json` — Non-sensitive settings (paths, flags)
- `db-stats.json` — Record counts (bookings, invoices, documents)
- `error-report.txt` — Last 50 errors with stack traces

**NOT included:**
- Database file
- PDF documents
- API keys
- Any business data

### Sharing with Developer
1. User exports diagnostic bundle
2. User sends zip file via email to developer
3. Developer analyzes logs to identify issue

---

## Distribution

Single customer distribution via GitHub Releases (unsigned build).

### Build & Release
```bash
pnpm tauri build
zip -r AIBookkeeper-v1.0.0.zip target/release/bundle/macos/AIBookkeeper.app
# Upload ZIP to GitHub Releases
```

### Customer Installation (One-Time)
1. Download ZIP from GitHub Releases
2. Extract and move `AIBookkeeper.app` to `/Applications/`
3. First launch: Right-click → Open → "Open Anyway"
4. Done (macOS remembers, won't ask again)

### Updates
1. You: Build new version, upload to GitHub Releases
2. Customer: Download, replace .app in Applications
3. Data persists (stored in `~/Library/Application Support/`)

*Note: No code signing or notarization. Suitable for single customer distribution.*

---

## Security Considerations

- **API Keys**: Stored in encrypted settings file (`settings.enc`) with machine-specific encryption key. On new machine, user re-enters API key.
- **No External Hosting**: All data remains local
- **Human Approval**: No automatic persistence without user confirmation
- **Audit Trail**: Domain events provide full traceability
- **Logs**: No sensitive data in logs; diagnostic bundle excludes business data

## Out of Scope

- Multi-user / server-based system
- Real-time ERP integration
- Fully automated processing (all operations require user confirmation)
