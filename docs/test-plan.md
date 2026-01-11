# Test Plan

This document defines the testing strategy for AI Bookkeeper, organized by layer following the hexagonal architecture.

## Testing Pyramid

```
        ┌─────────────┐
        │    E2E      │  Few, slow, high confidence
        ├─────────────┤
        │ Integration │  Adapters + repositories
        ├─────────────┤
        │  Use Cases  │  Application layer orchestration
        ├─────────────┤
        │    Unit     │  Domain logic, fast, many
        └─────────────┘
```

---

## 1. Unit Tests (Domain Layer)

Pure business logic, no external dependencies. Fast execution.

### 1.1 Entities

**Booking**
- Calculate total revenue from revenue_charges
- Calculate total costs from cost_charges
- Calculate margin (revenue - costs)
- Calculate margin percentage
- Calculate agent commission with custom rate
- Handle negative margin (costs > revenue)
- Add revenue charge updates totals
- Add cost charge updates totals
- Status transitions: PENDING → COMPLETE
- Status transition: COMPLETE → PENDING (revert)
- Booking ID is BL reference (editable)
- created_at set on first creation

**ClientInvoice**
- Invoice number unique per client
- Calculate total from charges
- Link to source document
- Store extraction metadata

**ProviderInvoice**
- Invoice number unique per provider
- Calculate total from charges
- Provider type assignment (SHIPPING, CARRIER, INSPECTION, OTHER)
- Link to source document
- Store extraction metadata

**Document**
- Status transitions: PENDING → PROCESSING → PROCESSED
- Status transitions: PENDING → PROCESSING → ERROR
- File hash calculation
- Store email reference
- Document type assignment (CLIENT_INVOICE, PROVIDER_INVOICE, OTHER)

**Client**
- NIF uniqueness
- Auto-creation from invoice data

**Provider**
- NIF uniqueness
- Provider type assignment
- Auto-creation from invoice data

**Company (Singleton)**
- Store NIF for classification
- Default commission rate 50%
- Custom commission rate

**Agent (Singleton)**
- Store profile info

**Settings (Singleton)**
- Store API key (encrypted reference)
- Store export path

### 1.2 Value Objects

**Money**
- Immutability
- Currency always EUR
- Addition of Money objects
- Subtraction of Money objects
- Multiplication by percentage

**BookingCharge**
- Immutability
- All required fields present
- Provider type for cost breakdown

**ClientInfo**
- Immutability
- Denormalized client data

**Port**
- Immutability
- Code and name

**FileHash**
- Immutability
- Algorithm and value
- Equality comparison (duplicate detection)

**EmailReference**
- Immutability
- Message ID, subject, sender, received_at

**ExtractionMetadata**
- Store AI model used
- Store confidence score
- Store raw JSON
- Track manually edited fields
- Store processed timestamp

**ErrorInfo**
- Error type and message
- Retryable flag
- Timestamp

### 1.3 Domain Services

**InvoiceClassifier**
- Issuer NIF = company NIF → ClientInvoice (revenue)
- Recipient NIF = company NIF → ProviderInvoice (cost)
- Unknown issuer NIF → create new Client
- Unknown provider NIF → create new Provider
- Detect provider type from invoice content

**DuplicateChecker**
- Same file hash → duplicate detected
- Different file hash → not duplicate
- Check across all documents

**InvoiceValidator**
- Required fields present → valid
- Missing invoice number → invalid
- Missing NIF → invalid
- Non-EUR currency → invalid (error)
- Missing BL reference → warning (user can complete)

---

## 2. Integration Tests (Adapters)

Test adapters against real infrastructure (SQLite, file system). Use test databases.

### 2.1 Repository Tests (SQLite)

**BookingRepository**
- Save and retrieve booking
- Update booking with new charges
- Find booking by ID (BL reference)
- Find or create booking
- List bookings with filters (client, date range, status)
- Sort bookings by date, margin, commission
- Charges stored as JSON

**InvoiceRepository**
- Save ClientInvoice
- Save ProviderInvoice
- Retrieve by invoice number + issuer
- Prevent duplicate invoice number per issuer
- List invoices with filters

**DocumentRepository**
- Save document
- Update document status
- Find by file hash (duplicate check)
- List pending documents
- List processed documents
- List error documents
- Find documents stuck in PROCESSING

**ClientRepository**
- Save client
- Find by NIF
- Prevent duplicate NIF
- List all clients

**ProviderRepository**
- Save provider
- Find by NIF
- Prevent duplicate NIF
- List all providers
- Filter by provider type

**CompanyRepository**
- Save company (singleton)
- Retrieve company
- Update company

**AgentRepository**
- Save agent (singleton)
- Retrieve agent
- Update agent

**SettingsRepository**
- Save settings
- Retrieve settings
- Update individual settings

### 2.2 External Service Tests (Mocked)

**AIExtractor (Mock)**
- Send PDF, receive structured JSON
- Handle text PDF extraction
- Handle image PDF extraction
- Return confidence scores
- Return document type
- Handle extraction errors
- Handle timeout
- Handle invalid API key
- Validate EUR currency in response

**EmailClient (Mock)**
- OAuth2 token refresh
- Fetch new emails
- Download PDF attachments
- Handle connection errors
- Handle authentication errors

**FileStorage**
- Save PDF to iCloud path
- Retrieve PDF
- Delete PDF
- Handle storage errors

**ReportGenerator**
- Generate Excel with booking data
- Generate Excel with commission summary
- Handle file write errors

**SecretStore (Mock)**
- Store API key securely
- Retrieve API key
- Handle keychain errors

---

## 3. Use Case Tests (Application Layer)

Test orchestration logic with mocked repositories and services.

### 3.1 Document Intake

**FetchEmails**
- Connect to Outlook via OAuth2
- Download new PDFs
- Create Document for each PDF
- Set status to PENDING
- Calculate file hash
- Skip already downloaded (by hash)
- Handle connection errors
- Handle no new emails

**ManageDocuments**
- List pending documents
- List processed documents
- List error documents
- Retry failed document (reset to PENDING)

### 3.2 Invoice Processing

**ProcessInvoice**
- Send PDF to AI extractor
- Detect document type
- Extract invoice data
- Classify as ClientInvoice or ProviderInvoice
- Create/update Client or Provider
- Find or create Booking by BL reference
- Add charges to booking
- Recalculate margin and commission
- Update document status to PROCESSED
- Handle AI extraction errors → status ERROR
- Handle non-EUR currency → status ERROR
- Handle missing data → user completes manually
- Track manually edited fields
- Validate before saving

**ReprocessInvoice**
- Re-send PDF to AI
- Replace extracted data
- Update processing timestamp
- Keep document status PROCESSED

### 3.3 Booking Management

**ListBookings**
- Return all bookings with financial summary
- Filter by client
- Filter by date range
- Filter by status (PENDING/COMPLETE)
- Sort by created_at
- Sort by margin
- Sort by commission

**ViewBookingDetail**
- Return booking with all charges
- Group cost charges by provider type
- Calculate commission with company rate
- Include links to source documents

**EditBooking**
- Update booking fields
- Update charge amounts
- Recalculate totals
- Cannot delete booking
- Cannot create booking manually

**MarkBookingComplete**
- Change status PENDING → COMPLETE
- Revert COMPLETE → PENDING

### 3.4 Reporting

**GenerateCommissionReport**
- Filter by date range
- Filter by status
- Calculate totals
- Export to Excel

**GenerateExcelReport**
- Filter by date, client, booking
- Include all relevant fields
- Save to specified path

**ExportBooking**
- Export single booking detail
- Include all charges
- Include financial summary

### 3.5 Configuration

**ConfigureAPIKey**
- Save API key to SecretStore
- Test connection to Claude API
- Return success/error
- Block AI features if invalid

**ConfigureCompany**
- Save company info
- NIF required
- Commission rate with default

**ConfigureAgent**
- Save agent profile

---

## 4. E2E Tests (Full Workflows)

Test complete user journeys through the API.

### 4.1 Happy Path: Complete Invoice Processing Workflow

```
1. Configure company NIF
2. Configure API key
3. Fetch emails → documents created
4. Process document → AI extracts data
5. Preview and confirm → invoice saved
6. Booking created with charges
7. Process more invoices → charges accumulate
8. Mark booking complete
9. Generate commission report
```

### 4.2 Incremental Booking Build-up

```
1. Process provider invoice (shipping) → booking created, costs €2,500
2. Process provider invoice (carrier) → same booking, costs €5,500
3. Process client invoice → same booking, revenue €6,500
4. Verify margin €1,000, commission €500
5. Mark complete
```

### 4.3 Error Recovery

```
1. Process document → AI fails
2. Document status = ERROR
3. User clicks retry
4. AI succeeds
5. Document status = PROCESSED
```

### 4.4 Manual Data Completion

```
1. Process document → AI extracts partial data
2. User completes missing fields
3. Manually edited fields tracked
4. Invoice saved successfully
```

### 4.5 Duplicate Prevention

```
1. Process document → success
2. Try to process same document again
3. Duplicate detected by file hash
4. Operation rejected
```

### 4.6 Non-Invoice Document

```
1. Process document (packing list)
2. AI detects type = OTHER
3. User can still complete data manually
4. Document marked PROCESSED
```

### 4.7 Crash Recovery

```
1. Start processing document
2. Status = PROCESSING
3. Simulate crash (document stuck)
4. Restart app
5. Warning shown for stuck documents
6. User retries
7. Processing completes
```

---

## 5. Test Data

### Sample Invoices (PDF fixtures)
- Text PDF: Standard provider invoice
- Text PDF: Client invoice with multiple line items
- Image PDF: Scanned shipping invoice
- Complex PDF: Carrier invoice with multiple bookings
- Non-invoice: Packing list

### Sample Data
- Company: NIF B12345678, 50% commission
- Client: Acme Mining, NIF A87654321
- Provider (Shipping): Mediterranean Lines, NIF B11111111
- Provider (Carrier): Express Transport, NIF B22222222
- Booking: BL-2024-001234

---

## 6. Test Environments

### Unit Tests
- No external dependencies
- In-memory only
- Run on every commit

### Integration Tests
- SQLite test database (reset per test)
- File system temp directory
- Mocked external services
- Run on every PR

### E2E Tests
- Full application stack
- Test database
- Mocked Outlook/Claude APIs
- Run before release

---

## 7. Coverage Goals

| Layer | Target |
|-------|--------|
| Domain (Unit) | 90%+ |
| Adapters (Integration) | 80%+ |
| Use Cases | 85%+ |
| E2E | Critical paths |
