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
- **Google Gemini 3 Pro** — Invoice data extraction (direct API)
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
         ┌─────────────────────┴─────────────────────┐
         │            DRIVEN ADAPTERS                │
         │  SQLite │ Google │ Outlook │ iCloud    │
         │  Excel  │ PDF                             │
         └───────────────────────────────────────────┘
```

For details on ports and domain model, see [application.md](application.md).

## Adapters

Adapters implement the ports defined in [application.md](application.md).

### Driven Adapters (Infrastructure)
Concrete implementations of output ports.

- **SQLite Adapter** — All repositories use local SQLite database (Alembic migrations)
- **Google Adapter** — Gemini 3 Pro API integration (direct Gemini API)
- **Outlook Adapter** — Microsoft Graph API with OAuth2 user consent (see OAuth2 details below)
- **iCloud Adapter** — Local filesystem in iCloud Drive folder (manual cleanup, user responsibility)
- **Excel Adapter** — Generate .xlsx files using openpyxl
- **PDF Adapter** — pypdf for text extraction; scanned PDFs sent as images directly to Gemini 3

#### PDF Processing Limits
- **Max file size**: 20 MB
- **Max pages**: 50 pages
- **Image conversion**: 300 DPI, PNG format for scanned pages

#### OAuth2 Implementation (Microsoft Graph)

**Required Scopes:**
- `Mail.Read` — Read user's mail
- `Mail.ReadBasic` — Read basic mail properties
- `User.Read` — Sign in and read user profile
- `offline_access` — Maintain access (refresh tokens)

**Token Storage:**
- Access token and refresh token stored in SQLite Settings table
- Tokens are encrypted at rest using system keychain (macOS Keychain Services)
- Token fields: `outlook_access_token`, `outlook_refresh_token`, `outlook_token_expiry`

**Token Refresh Flow:**
1. Before each email fetch, check if access token expires within 5 minutes
2. If expiring, use refresh token to obtain new access token
3. If refresh fails (token revoked, expired), set `outlook_configured = false`
4. User sees "Outlook disconnected" in Settings, must re-authenticate

**Re-authentication:**
- User clicks "Connect Account" in Settings
- Opens system browser for Microsoft OAuth consent
- App receives authorization code via localhost redirect
- Exchanges code for tokens, stores encrypted

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
| **AI API** | Real Gemini 3 API (dev key) or mock responses |
| **Outlook** | Mock email client (no real OAuth) |
| **File Storage** | Local temp folder: `data/pdfs/` |
| **Logging** | DEBUG level, structured JSON (console + file output) |

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
| **AI API** | Real Gemini 3 API (staging key) |
| **Outlook** | Real OAuth (test account) |
| **File Storage** | iCloud Drive staging folder |
| **Logging** | INFO level, structured JSON file output |
| **Updates** | Manual distribution (DMG/ZIP) |

Used for:
- Testing full workflows with real APIs
- Beta user feedback
- Pre-release validation

### Production
Released application for end users.

| Component | Configuration |
|-----------|---------------|
|| **App** | Unsigned build (single customer distribution) |
| **Database** | SQLite: `~/Library/Application Support/AIBookkeeper/data.db` |
| **AI API** | User's own Gemini API key |
| **Outlook** | Real OAuth (user's account) |
| **File Storage** | iCloud Drive: `~/Library/Mobile Documents/com~apple~CloudDocs/AIBookkeeper/` |
| **Logging** | INFO level (DEBUG disabled), structured JSON file output |
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
- External API calls (Outlook, Gemini 3) with status codes
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

### Redaction and Sanitization
- Logging applies centralized redaction before writing records.
- Structured context is sanitized recursively (including nested objects/lists).
- Sensitive keys/patterns are redacted (API keys, tokens, auth headers, NIF, email, phone, address, sender/subject, extraction payloads, financial fields).
- Free-text log messages are sanitized using sensitive-value pattern matching.

### Log Rotation
- One file per day (`app-YYYY-MM-DD.log`)
- Retention: 30 days
- Older files auto-deleted on startup

### Export Diagnostic Bundle
User can generate a diagnostic bundle for developer support:

**Settings → Help → Export Diagnostics**

Export destination:
- `~/Library/Application Support/AIBookkeeper/diagnostics/`

Bundle contents (`diagnostics-YYYYMMDD-HHMMSS.zip`):
- `logs/` — Last 5 log files
- `app-info.json` — App version, OS version, Python version
- `config-summary.json` — Non-sensitive settings (paths, flags)
- `db-stats.json` — Record counts (bookings, invoices, documents)
- `error-report.txt` — Last 50 errors with stack traces

Export constraints:
- For large logs, only the last 2 MB per selected log file is included.
- If truncation occurs, bundle includes `logs/TRUNCATION_NOTES.txt`.
- Export can include logs from legacy `storage_path/logs` as fallback when present.

**NOT included:**
- Database file
- PDF documents
- API keys or tokens
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

- **API Keys**: Gemini API key stored in SQLite database (Settings table). Stored as plaintext but protected by:
  - Database file is local-only in `~/Library/Application Support/AIBookkeeper/`
  - Standard macOS file permissions (user-only read/write)
  - App sandbox (when distributed via notarized build)
  - *Future consideration*: Migrate to macOS Keychain for sensitive credentials
- **OAuth Tokens**: Outlook tokens encrypted using macOS Keychain Services before storage
- **No External Hosting**: All data remains local
- **Human Approval**: No automatic persistence without user confirmation
- **Audit Trail**: Domain events provide full traceability
- **Logs**: No sensitive data in logs; diagnostic bundle excludes business data
- **PDF Content**: Invoice PDFs stored locally in iCloud Drive; no cloud processing except Gemini 3 API calls

## Out of Scope

- Multi-user / server-based system
- Real-time ERP integration
- Fully automated processing (all operations require user confirmation)
