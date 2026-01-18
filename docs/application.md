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
| **ProcessInvoiceBatch** | Process multiple selected documents sequentially with defined failure handling. | HU-IA2 |
| **ReprocessInvoice** | Re-extract data from already processed document | HU-IA7 |

### Booking Management

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **ListBookings** | View all bookings with financial status, filter/sort | HU4.1 |
| **ViewBookingDetail** | Show booking with charges breakdown and commission | HU4.2 |
| **EditBooking** | Edit booking data after saving (no delete, no manual creation) | — |
| **MarkBookingComplete** | Change status from PENDING → COMPLETE | HU4.4 |

**EditBooking Field Permissions:**
- ✅ Editable: `id` (BL reference), `client`, `pol`, `pod`, `vessel`, `containers`, `status`
- ✅ Editable: Individual charge `description`, `amount`, `charge_category`
- ❌ Not editable: `created_at`, `invoice_number`, `invoice_date`, source document links
- ❌ Not allowed: Delete charges, delete invoices, create charges manually
- ⚠️ Recalculation: Editing charge amounts triggers automatic recalculation of booking totals/margin

*Note: HU4.3 (incremental invoice attribution) is handled by ProcessInvoice — it finds or creates bookings automatically.*

### Reporting

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **GenerateCommissionReport** | Commission summary for date range, export to Excel | HU4.5 |
| **GenerateExcelReport** | Export filtered data (by date, client, booking) | HU7.1 |
| **ExportBooking** | Export single booking detail to Excel | HU7.2 |

**Report Date Filtering:**
- Commission Report: Filters by `booking.created_at` (when first invoice arrived)
- Excel Report: User selects date field — `booking.created_at` OR `invoice.invoice_date`
- Default: `booking.created_at` for consistency

### Configuration

| Use Case | Description | User Stories |
|----------|-------------|--------------|
| **ConfigureAPIKey** | Set Anthropic API key, test connection | HU-IA1 |
| **ConfigureCompany** | Set company NIF (for invoice classification) and commission rate | HU5.1 |
| **ConfigureAgent** | Set agent profile (name, email, phone) | HU5.2 |
| **ConfigurePrompt** | Edit AI extraction prompt template with validation | — |

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
Day 1: Shipping line invoice → Booking CREATED (PENDING), Costs: €2,500
Day 3: Carrier invoice       → Booking UPDATED, Costs: €5,500  
Day 5: Client invoice        → Booking UPDATED, Revenue: €6,500, Margin: €1,000
       User marks COMPLETE   → Commission: €500
```

**Status Flow:** `PENDING ↔ COMPLETE` (reversible — user can revert to PENDING if more invoices arrive)

### Multi-Booking Invoice Handling

A single provider invoice (e.g., carrier) may contain charges for **multiple bookings**. The AI extracts charges with their `bl_reference`. Processing rules:

1. **Charge allocation**: Each charge is attributed to its specific booking by `bl_reference`
2. **Tax allocation**: Taxes are distributed **proportionally** by charge amount per booking
3. **Invoice totals**: The full invoice total is stored on the invoice entity; individual booking views show only their portion
4. **Invoice linkage**: The same invoice appears linked to multiple bookings (with different charge subsets)

Example: Invoice with €1,000 total (BL-001: €600, BL-002: €400, Tax: €210)
- BL-001 receives: €600 charges + €126 tax (60%)
- BL-002 receives: €400 charges + €84 tax (40%)

### Document Type OTHER Handling

When AI detects a document that is not an invoice (packing list, bill of lading, etc.):

1. Document status set to **PROCESSED** with type **OTHER**
2. User sees a simplified view with:
   - Document metadata (filename, date, sender)
   - AI's extraction notes explaining why it's not an invoice
   - Option to **Override**: manually classify as CLIENT_INVOICE or PROVIDER_INVOICE
3. If overridden, user must manually fill all required invoice fields
4. OTHER documents are **not** linked to bookings unless overridden and completed

### Non-EUR Currency Handling

All amounts must be in EUR. When AI detects a non-EUR currency:

1. `currency_valid` is set to `false` in extraction result
2. Document status set to **ERROR** with error type `INVALID_CURRENCY`
3. User sees error message: "Invoice currency is {detected_currency}. Only EUR invoices are supported."
4. User options:
   - **Dismiss**: Mark document as not processable (stays in ERROR)
   - **Override**: Manually enter EUR amounts (original currency noted in extraction_metadata)

*Note: No automatic currency conversion. User must obtain EUR-equivalent amounts externally.*

### Scanned PDF Detection

PDF processing flow:

1. **Text extraction attempt**: Use pypdf to extract text
2. **Detection criteria**: If extracted text is < 100 characters or contains mostly gibberish (high ratio of non-alphanumeric characters), PDF is considered scanned
3. **Scanned handling**: Convert each page to PNG (300 DPI, RGB) and send as images to Claude
4. **Hybrid PDFs**: Some pages text, some scanned — extract text where available, send images for scanned pages
5. **Page limit**: Max 50 pages; if exceeded, reject with error before sending to AI

### Batch Processing Behavior

When user selects multiple documents and clicks "Process Selected":

1. **Sequential processing**: Documents are processed one at a time (not in parallel) to avoid API rate limits and allow user review
2. **Per-document modal**: After each AI extraction, the Process Invoice modal opens for user review
3. **User actions per document**:
   - **Save & Continue**: Save invoice, proceed to next document
   - **Skip**: Leave document as PENDING, proceed to next
   - **Cancel Batch**: Stop processing remaining documents (already-saved invoices are kept)
4. **Failure handling**:
   - If AI extraction fails → document marked ERROR, user sees error message, batch continues to next document
   - If user closes modal without action → document stays PENDING, batch continues
5. **Progress indicator**: "Processing 3 of 7 documents" shown in modal header
6. **Batch summary**: After all documents processed, toast shows "Processed 5 invoices, 1 skipped, 1 error"

### Prompt Customization Validation

When user edits the extraction prompt in Settings:

1. **Schema validation**: Before saving, the app sends a test request to Claude with a sample PDF
2. **Response validation**: The response must:
   - Be valid JSON
   - Contain required top-level fields: `document_type`, `invoice`
   - Contain required invoice fields: `invoice_number`, `issuer`, `recipient`, `charges`, `totals`
3. **Validation feedback**:
   - ✅ "Prompt validated successfully" → Save enabled
   - ❌ "Invalid prompt: missing field 'charges'" → Save disabled, error shown
4. **Test PDF**: A built-in sample invoice PDF is used for validation (not user documents)
5. **Reset option**: "Reset to Default" restores the original prompt template

*Note: Validation uses a real Claude API call, so requires valid API key.*

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
- `invoice_number` (unique per issuer — i.e., per client), `client_id`, `invoice_date`
- `bl_reference`, `total_amount`, `tax_amount`
- `charges[]`, `source_document`, `extraction_metadata`

### ProviderInvoice (Cost)
- `invoice_number` (unique per issuer — i.e., per provider), `provider_id`, `invoice_date`
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

**Client Auto-creation Rules:**
- Required: `nif` (must be non-empty after NIF normalization)
- Optional: `name` (defaults to "Unknown Client" if not extracted)
- If NIF matches existing client, reuse existing record (no duplicate)
- Client name can be updated later via booking edit

### Provider
- `name`, `nif` (unique), `provider_type` (SHIPPING, CARRIER, INSPECTION, OTHER)
- Auto-created when processing provider invoices

**Provider Auto-creation Rules:**
- Required: `nif` (must be non-empty after NIF normalization)
- Required: `provider_type` (defaults to OTHER if AI cannot determine)
- Optional: `name` (defaults to "Unknown Provider" if not extracted)
- If NIF matches existing provider, reuse existing record
- Provider type can be corrected later; changes do NOT affect historical charges

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
| **BookingCharge** | `booking_id`, `invoice_id`, `charge_category`, `provider_type`, `container`, `description`, `amount` |
| **ClientInfo** | `client_id`, `name`, `nif` (denormalized in Booking) |
| **Port** | `code`, `name` |
| **FileHash** | `algorithm`, `value` |
| **EmailReference** | `message_id`, `subject`, `sender`, `received_at` |

*Note: Email body is NOT stored. Only metadata needed for deduplication and display. Subject stored for potential future search/filtering.*
| **DocumentReference** | `document_id`, `filename`, `file_hash` |
| **ExtractionMetadata** | `ai_model`, `overall_confidence`, `field_confidences`, `raw_json`, `manually_edited_fields`, `processed_at` |
| **ErrorInfo** | `error_type`, `error_message`, `occurred_at`, `retryable` |

## Enums

| Enum | Values |
|------|--------|
| **BookingStatus** | PENDING, COMPLETE |
| **ProcessingStatus** | PENDING, PROCESSING, PROCESSED, ERROR |
| **DocumentType** | CLIENT_INVOICE, PROVIDER_INVOICE, OTHER |
| **ProviderType** | SHIPPING, CARRIER, INSPECTION, OTHER |
| **ChargeCategory** | FREIGHT, HANDLING, DOCUMENTATION, TRANSPORT, INSPECTION, INSURANCE, OTHER |
| **ConfidenceLevel** | HIGH, MEDIUM, LOW |
| **ErrorType** | NIF_NOT_CONFIGURED, API_KEY_MISSING, API_KEY_INVALID, OUTLOOK_DISCONNECTED, AI_TIMEOUT, AI_RATE_LIMIT, FILE_TOO_LARGE, TOO_MANY_PAGES, DISK_FULL, ICLOUD_UNAVAILABLE, DUPLICATE_DOCUMENT, INVALID_CURRENCY |

### Charge Category to Provider Type Mapping

When creating `BookingCharge` from AI extraction, the `charge_category` comes directly from AI. The `provider_type` is determined by the invoice's provider, not the charge category. Both are stored for reporting flexibility:

- `charge_category`: What type of service (FREIGHT, TRANSPORT, etc.)
- `provider_type`: Who provided it (SHIPPING, CARRIER, etc.)

### Confidence Aggregation

`overall_confidence` is calculated as the **minimum** confidence of critical fields:
- `document_type_confidence`
- `invoice_number_confidence`
- `issuer.nif_confidence`
- `recipient.nif_confidence`
- `total_confidence`

Mapping: HIGH = 100%, MEDIUM = 70%, LOW = 40%. The overall percentage shown in UI is the minimum of these values.

---

## Domain Services

| Service | Purpose |
|---------|---------|
| **InvoiceClassifier** | Classify invoice as ClientInvoice/ProviderInvoice based on NIF |
| **DuplicateChecker** | Detect duplicate invoices by file hash |
| **InvoiceValidator** | Validate extracted data completeness |

---

## Error Handling

### Pre-condition Errors

These errors block operations and require user action:

| Error | When | User Action |
|-------|------|-------------|
| **NIF_NOT_CONFIGURED** | ProcessInvoice called without company NIF | Modal: "Configure company NIF in Settings before processing invoices" |
| **API_KEY_MISSING** | ProcessInvoice called without Anthropic API key | Modal: "Configure API key in Settings" |
| **API_KEY_INVALID** | Claude returns 401 Unauthorized | Toast error + redirect to Settings, API key field highlighted |
| **OUTLOOK_DISCONNECTED** | FetchEmails called with invalid/expired OAuth | Toast: "Outlook disconnected" + Settings shows reconnect button |

### Runtime Errors

| Error | When | Behavior |
|-------|------|----------|
| **AI_TIMEOUT** | Claude API call exceeds 60s | Document → ERROR, retryable=true |
| **AI_RATE_LIMIT** | Claude returns 429 | Document → ERROR, show "Try again in X minutes", retryable=true |
| **FILE_TOO_LARGE** | PDF > 20MB | Document → ERROR, retryable=false, message shows limit |
| **TOO_MANY_PAGES** | PDF > 50 pages | Document → ERROR, retryable=false |
| **DISK_FULL** | Cannot save PDF to iCloud | Toast error: "Disk full. Free up space and retry." Document stays PENDING |
| **ICLOUD_UNAVAILABLE** | iCloud Drive not accessible | Toast warning: "iCloud unavailable. PDFs saved locally." Fallback to `~/Documents/AIBookkeeper/` |
| **DUPLICATE_DOCUMENT** | File hash already exists | Toast info: "Document already imported." Skip silently during fetch |

### API Key Expiry Mid-Batch

If API key becomes invalid during batch processing:
1. Current document → ERROR with `API_KEY_INVALID`
2. Batch processing stops immediately
3. User sees modal: "API key invalid. Configure in Settings to continue."
4. Remaining documents stay PENDING

---

## Domain Events

| Event | When |
|-------|------|
| **DocumentReceived** | New PDF downloaded from email |
| **InvoiceProcessed** | AI extraction completed successfully |
| **ExtractionFailed** | AI extraction failed |
| **BookingUpdated** | Charges added to booking, margin recalculated |
