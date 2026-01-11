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
│     Click "Search new invoices" → App finds PDFs in your email │
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
- **AI**: Anthropic Claude Sonnet 4.5 API
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

## License

See [LICENSE](LICENSE) for details.
