# AI Bookkeeper

A local macOS desktop application for automated invoice processing using AI.

## What Does This Software Do?

As a commercial agent in maritime freight forwarding, you receive invoices from multiple sources:
- **Client invoices** you issue (e.g., to your mining or manufacturing clients) → your **revenue**
- **Provider invoices** from shipping lines, land carriers, inspection companies → your **costs**

Your commission is calculated per **booking**: `(Revenue - Costs) × 50%`

**The problem**: Invoices for the same booking arrive on different days, from different providers, in different formats. Manually tracking which costs belong to which booking is time-consuming and error-prone.

**AI Bookkeeper solves this by:**

1. **Detecting new invoices** from your dedicated Outlook account
2. **Reading PDFs automatically** using AI — even scanned invoices
3. **Classifying invoices** as revenue or cost based on your company's NIF
4. **Grouping charges by booking** as invoices arrive over days/weeks
5. **Calculating your commission** when all invoices for a booking are received
6. **Generating Excel reports** for Finance or your own records

### Your Daily Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│  1. RECEIVE                                                     │
│     Click "Fetch Emails" → App finds PDFs in your email        │
├─────────────────────────────────────────────────────────────────┤
│  2. PROCESS                                                     │
│     Select pending documents → AI extracts all the data         │
│     Review extracted fields → Confirm or correct before saving  │
├─────────────────────────────────────────────────────────────────┤
│  3. TRACK                                                       │
│     View bookings with accumulated revenue and costs            │
│     Mark booking as "Complete" when all invoices are in         │
├─────────────────────────────────────────────────────────────────┤
│  4. REPORT                                                      │
│     Generate commission reports by date range                   │
│     Export to Excel for Finance                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Example: Booking BK-001234

| Day | Invoice Received | Type | Amount | Running Margin |
|-----|------------------|------|--------|----------------|
| Mon | Shipping line (ocean freight) | Cost | €2,500 | -€2,500 |
| Wed | Land carrier (container transport) | Cost | €3,000 | -€5,500 |
| Fri | Your invoice to client | Revenue | €6,500 | **€1,000** |

**Your commission**: €1,000 × 50% = **€500**

All of this is tracked automatically as invoices arrive.

## Key Features

- **Automatic Email Detection**: Monitors a dedicated Outlook account for new invoices
- **AI-Powered PDF Processing**: Extracts booking numbers, clients, POL/POD, containers, amounts, etc.
- **Local SQLite Database**: Single source of truth for all invoice data
- **On-Demand Excel Reports**: Generate filtered reports directly from the database
- **Human-in-the-Loop**: All operations require user confirmation before saving

## Tech Stack

- **Frontend**: Tauri + Vue 3 + PrimeVue + Tailwind CSS
- **Backend**: Python (REST API)
- **Database**: SQLite
- **AI**: Google Gemini 3 Pro API
- **Storage**: iCloud Drive for PDFs and reports

## Documentation

- [User Stories](docs/user-stories.md) - Complete list of epics and user stories
- [Application](docs/application.md) - Use cases and domain model
- [Architecture](docs/architecture.md) - Technical design (hexagonal architecture, ports, adapters)
- [UX Design](docs/ux-design.md) - Screens, navigation, user flows
- [Test Plan](docs/test-plan.md) - Testing strategy by layer
- [Extraction Prompt](docs/extraction-prompt.md) - Default AI prompt template (user-editable)

## Project Status

🚧 **In Development** - See [docs/](docs/) for detailed specifications.

## Development

### Prerequisites

- **macOS** 12 (Monterey) or later
- **Rust** (install via [rustup](https://rustup.rs/))
- **Python 3.11+** (install via Homebrew: `brew install python@3.11`)
- **Node.js 20+** (install via Homebrew: `brew install node`)
- **pnpm** (install via npm: `npm install -g pnpm`)
- **uv** (Python package manager, install via: `curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Clone and Setup

```bash
# Clone the repository
git clone https://github.com/your-username/ai-bookkeeper.git
cd ai-bookkeeper

# Copy environment template
cp .env.development .env

# Install Python dependencies
uv sync --all-extras

# Install frontend dependencies
cd src/frontend
pnpm install
cd ../..
```

### Running the Application

**Backend only (API server):**
```bash
uv run uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

**Frontend only (development):**
```bash
cd src/frontend
pnpm dev
```

**Full Tauri app (development):**
```bash
cd src/frontend
pnpm tauri dev
```

### Running Tests

**Backend tests:**
```bash
uv run pytest tests -v
```

**Backend tests with coverage:**
```bash
uv run pytest tests -v --cov=src/backend --cov-report=term-missing
```

**Linting and type checking:**
```bash
uv run ruff check src/backend tests
uv run mypy src/backend
```

**Frontend type checking:**
```bash
cd src/frontend
pnpm vue-tsc --noEmit
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_ENV` | Environment (development/production/test) | `development` |
| `DEBUG` | Enable debug mode | `false` |
| `API_HOST` | API server host | `127.0.0.1` |
| `API_PORT` | API server port | `8000` |
| `DATABASE_URL` | SQLite database URL | `sqlite:///data/ai_bookkeeper.db` |
| `GEMINI_API_KEY` | Gemini API key (optional, can configure in UI) | - |
| `AZURE_CLIENT_ID` | Azure AD app client ID for Outlook | - |
| `AZURE_TENANT_ID` | Azure AD tenant ID | `common` |
| `ICLOUD_ENABLED` | Enable iCloud Drive for PDF storage | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Azure App Registration (for Outlook)

To enable email fetching from Outlook:

1. Go to [Azure Portal](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Register a new application
3. Set redirect URI: `http://localhost:8000/api/settings/outlook/callback`
4. Add API permissions: `Mail.Read`, `Mail.ReadBasic`, `User.Read`, `offline_access`
5. Copy the Client ID to your `.env` file as `AZURE_CLIENT_ID`

> **Note**: This is free - no API costs for reading emails.

### Project Structure

```
ai-bookkeeper/
├── src/
│   ├── backend/              # Python FastAPI backend
│   │   ├── domain/           # Business logic (entities, value objects, services)
│   │   ├── application/      # Use cases
│   │   ├── ports/            # Interfaces (input/output)
│   │   ├── adapters/         # Implementations (API, persistence, external)
│   │   └── config/           # Configuration
│   └── frontend/             # Tauri + Vue 3 frontend
│       ├── src/              # Vue components, views, stores
│       └── src-tauri/        # Tauri configuration
├── tests/                    # Backend tests
├── docs/                     # Documentation
└── data/                     # Local database (gitignored)
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

See [LICENSE](LICENSE) for details.
