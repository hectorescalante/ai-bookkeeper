# Application Design

This document describes the application layer: use cases and the domain model they operate on.

## Use Cases

Use cases orchestrate domain entities to fulfill user stories. Each use case maps to one or more user stories.

### Document Intake

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **FetchEmails** | Connect to Outlook, download PDF attachments, create Documents | HU1.1, HU1.2 |
| **ManageDocuments** | List pending/processed/error documents, retry failed ones | HU2.1, HU2.2, HU2.3 |

### Invoice Processing

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **ProcessInvoice** | Send PDF to AI, detect document type, extract data, preview for validation, classify by NIF, attribute to bookings. User can complete missing data manually. | HU-IA2, HU-IA3, HU-IA4, HU-IA5, HU-IA6, HU-IA8 |
| **ReprocessInvoice** | Re-extract data from already processed document | HU-IA7 |

### Booking Management

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **ListBookings** | View all bookings with financial status, filter/sort | HU4.1 |
| **ViewBookingDetail** | Show booking with charges breakdown and commission | HU4.2 |
| **EditBooking** | Edit booking data after saving (no delete, no manual creation) | — |
| **MarkBookingComplete** | Change status from PENDING → COMPLETE | HU4.4 |

*Note: HU4.3 (incremental invoice attribution) is handled by ProcessInvoice — it finds or creates bookings automatically.*

### Reporting

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **GenerateCommissionReport** | Commission summary for date range, export to Excel | HU4.5 |
| **GenerateExcelReport** | Export filtered data (by date, client, booking) | HU7.1 |
| **ExportBooking** | Export single booking detail to Excel | HU7.2 |

### Configuration

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **ConfigureAPIKey** | Set Anthropic API key, test connection | HU-IA1 |
| **ConfigureCompany** | Set company NIF (for invoice classification) and commission rate | HU5.1 |
| **ConfigureAgent** | Set agent profile (name, email, phone) | HU5.2 |
| **ConfigurePrompt** | Edit AI extraction prompt template | — |

---

## Ports

Ports define the boundaries of the application — what it exposes (input) and what it needs (output).

### Input Ports (Use Cases)
Interfaces that define what the application can do. Grouped by domain area.

**Document Intake:**
- **FetchEmails** — Connect to Outlook, download PDF attachments
- **ManageDocuments** — List pending/processed/error documents, retry failed

**Invoice Processing:**
- **ProcessInvoice** — Extract data from PDF, classify, attribute to bookings
- **ReprocessInvoice** — Re-extract data from already processed document

**Booking Management:**
- **ListBookings** — View all bookings with financial status, filter/sort
- **ViewBookingDetail** — Show booking with charges breakdown and commission
- **EditBooking** — Edit booking/invoice data after saving
- **MarkBookingComplete** — Change status from PENDING → COMPLETE

*Note: No deletion or manual creation of bookings/invoices. All data originates from processed documents.*

**Reporting:**
- **GenerateCommissionReport** — Commission summary for date range
- **GenerateExcelReport** — Export filtered data to Excel
- **ExportBooking** — Export single booking detail to Excel

**Configuration:**
- **ConfigureAPIKey** — Set Anthropic API key, test connection
- **ConfigureCompany** — Set company NIF and commission rate
- **ConfigureAgent** — Set agent profile
- **ConfigurePrompt** — Edit AI extraction prompt template

### Output Ports (Repositories & External Services)
Interfaces that the domain needs from the outside world.

**Repositories:**
- **BookingRepository** — Primary aggregate persistence
- **InvoiceRepository** — ClientInvoice and ProviderInvoice persistence
- **DocumentRepository** — PDF document tracking
- **ClientRepository** — Client persistence (auto-created from invoices)
- **ProviderRepository** — Provider persistence (auto-created from invoices)
- **CompanyRepository** — Company singleton
- **AgentRepository** — Agent singleton
- **SettingsRepository** — Application settings

**External Services:**
- **AIExtractor** — Send PDF to Claude, receive structured data
- **EmailClient** — Fetch emails from Outlook
- **FileStorage** — Store/retrieve PDFs (iCloud Drive)
- **ReportGenerator** — Generate Excel files
- **SecretStore** — Encrypted settings file with machine-specific key

---

## Domain Model

### Core Concept: Booking as Primary Aggregate

**Booking** is the central business concept. Commission is calculated per booking:

```
MARGIN = Revenue (Client Invoices) − Costs (Provider Invoices)
AGENT COMMISSION = 50% × Margin
```

*Note: Negative margins (and commissions) are allowed when costs exceed revenue.*

*Currency: All amounts are in EUR. AI extraction validates currency and flags non-EUR invoices as errors.*

Invoices are **source documents** that contribute charges to bookings. A single provider invoice may contain charges for multiple bookings.

### Incremental Invoice Processing

Invoices for the same booking arrive on **different days**:

```
Day 1: Shipping line invoice → Booking CREATED (OPEN), Costs: €2,500
Day 3: Carrier invoice       → Booking UPDATED, Costs: €5,500  
Day 5: Client invoice        → Booking UPDATED, Revenue: €6,500, Margin: €1,000
       User marks COMPLETE   → Commission: €500
```

**Status Flow:** `PENDING → COMPLETE`

---

## Entities

### Booking (Primary Aggregate)
- `id` — BL reference extracted from invoice (editable by user)
- `created_at` — when booking was first created (first invoice arrived)
- `client: ClientInfo`, `pol`, `pod`, `vessel`, `containers`
- `revenue_charges[]`, `cost_charges[]` — aggregated from invoices
- `status` — PENDING, COMPLETE
- Properties: `total_revenue`, `total_costs`, `margin`, `margin_percentage`
- Method: `calculate_agent_commission(rate)`

### ClientInvoice (Revenue)
- `invoice_number` (unique per client), `client_id`, `invoice_date`
- `bl_reference`, `total_amount`, `tax_amount`
- `charges[]`, `source_document`, `extraction_metadata`

### ProviderInvoice (Cost)
- `invoice_number` (unique per provider), `provider_id`, `invoice_date`
- `bl_reference`, `total_amount`, `tax_amount`
- `charges[]`, `source_document`, `extraction_metadata`

### Document
- `email_reference`, `filename`, `file_hash`
- `document_type` — detected by AI (CLIENT_INVOICE, PROVIDER_INVOICE, OTHER)
- `status` — PENDING, PROCESSING, PROCESSED, ERROR
- `storage_path`, `error_info`

*Recovery: Documents stuck in PROCESSING (e.g., after crash) show a warning on startup. User can retry.*

### Client
- `name`, `nif` (unique)
- Auto-created when processing client invoices

### Provider
- `name`, `nif` (unique), `provider_type` (SHIPPING, CARRIER, INSPECTION, OTHER)
- Auto-created when processing provider invoices

### Company (Singleton)
- `name`, `nif` — used to classify invoices (issuer NIF = ours → revenue)
- `agent_commission_rate` — default 50%

### Agent (Singleton)
- `name`, `email`, `phone`

### Settings (Singleton)
- `anthropic_api_key`, `outlook_configured`, `default_export_path`
- `extraction_prompt` — User-editable prompt template for Claude invoice extraction

---

## Value Objects

| Value Object | Fields |
|--------------|--------|
| **Money** | `amount`, `currency` (always EUR) |
| **BookingCharge** | `booking_id`, `invoice_id`, `provider_type`, `container`, `description`, `amount` |
| **ClientInfo** | `client_id`, `name`, `nif` (denormalized in Booking) |
| **Port** | `code`, `name` |
| **FileHash** | `algorithm`, `value` |
| **EmailReference** | `message_id`, `subject`, `sender`, `received_at` |
| **DocumentReference** | `document_id`, `filename`, `file_hash` |
| **ExtractionMetadata** | `ai_model`, `confidence`, `raw_json`, `manually_edited_fields`, `processed_at` |
| **ErrorInfo** | `error_type`, `error_message`, `occurred_at`, `retryable` |

## Enums

| Enum | Values |
|------|--------|
| **BookingStatus** | PENDING, COMPLETE |
| **ProcessingStatus** | PENDING, PROCESSING, PROCESSED, ERROR |
| **DocumentType** | CLIENT_INVOICE, PROVIDER_INVOICE, OTHER |
| **ProviderType** | SHIPPING, CARRIER, INSPECTION, OTHER |

---

## Domain Services

| Service | Purpose |
|---------|---------|
| **InvoiceClassifier** | Classify invoice as ClientInvoice/ProviderInvoice based on NIF |
| **DuplicateChecker** | Detect duplicate invoices by file hash |
| **InvoiceValidator** | Validate extracted data completeness |

---

## Domain Events

| Event | When |
|-------|------|
| **DocumentReceived** | New PDF downloaded from email |
| **InvoiceProcessed** | AI extraction completed successfully |
| **ExtractionFailed** | AI extraction failed |
| **BookingUpdated** | Charges added to booking, margin recalculated |
