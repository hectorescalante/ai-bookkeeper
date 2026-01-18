# User Stories

## EPIC 1 – Outlook Email Reading

### HU1.1 – Connect Dedicated Outlook Account
**As** a commercial agent  
**I want** to connect my dedicated invoice Outlook account  
**So that** the app can automatically detect new documents

**Acceptance Criteria:**
- OAuth2 authentication with user consent (Microsoft login flow)
- Only requires authorization once (token refresh handled automatically)
- The entire inbox is considered the invoice source
- **Manual polling only** ("Fetch Emails" button, no automatic background polling)

### HU1.2 – Detect New Emails with Invoices
**As** a commercial agent  
**I want** the app to detect new emails with PDFs  
**So that** I avoid manual downloads

**Acceptance Criteria:**
- "Fetch Emails" button on the Documents screen
- Emails with PDF attachments are added to the pending documents list
- **Multiple attachments:** all PDFs from an email are processed individually

---

## EPIC 2 – Document Management (Pending, Processed, Errors)

### HU2.1 – View Pending Documents
**As** a commercial agent  
**I want** to see detected documents that haven't been processed yet  
**So that** I can decide which ones to process

**Acceptance Criteria:**
- View with date, sender, subject, number of PDFs
- Allows multiple selection and "Process" button

### HU2.2 – View Processed Documents
**As** a commercial agent  
**I want** to see a history of processed invoices  
**So that** I have traceability

**Acceptance Criteria:**
- List with invoice type, booking, amounts, and PDF links
- Filter by date, client, booking, or type

### HU2.3 – View Documents with Errors
**As** a commercial agent  
**I want** to identify documents that failed processing  
**So that** I can correct them manually or reprocess them

**Acceptance Criteria:**
- Dedicated view with error message and "Retry" or "Edit manually" buttons

---

## EPIC 3 – AI Invoice Processing (Claude Sonnet 4.5)

### HU-IA1 – Configure Anthropic API Key
**As** a commercial agent  
**I want** to enter my Anthropic key (Claude Sonnet 4.5)  
**So that** the application can process invoices with AI

**Acceptance Criteria:**
- Configuration screen has a field for the Anthropic API key
- User can click "Test connection" and the app:
  - Makes a test request to Claude Sonnet 4.5
  - Shows "Valid connection" if successful
- The key is stored in the local SQLite database
- If the key is invalid, the app shows a clear error and blocks the AI module

### HU-IA2 – Process PDF with AI (Text or Images)
**As** a commercial agent  
**I want** the app to process PDF invoices (even scanned ones) using Claude Sonnet 4.5  
**So that** I automatically get relevant data without manual transcription

**Acceptance Criteria:**
- When selecting a pending PDF and clicking "Process", the app:
  - Extracts text from PDF using pypdf (if digital)
  - Or sends PDF images directly to Claude Sonnet 4.5 (if scanned, no local OCR)
- **Limits:** Max 20MB file size, max 50 pages per PDF
- Claude Sonnet 4.5 returns a structured JSON with main fields:
  - Invoice type
  - Booking
  - Client
  - POL/POD
  - Shipping company / Supplier
  - Containers
  - Amounts (Shipping, Transport, Insurance, Others)
  - Invoice date
  - Detailed items (if applicable)
- The process must work with:
  - Text PDFs
  - Image PDFs (scanned)
  - Invoices with tables or complex text blocks

### HU-IA3 – Automatic Invoice Classification by NIF
**As** a commercial agent  
**I want** the app to automatically classify invoices as ClientInvoice (revenue) or ProviderInvoice (cost)  
**So that** charges are correctly attributed to bookings

**Acceptance Criteria:**
- The AI extracts issuer and recipient NIF from the PDF
- Classification is automatic based on company NIF:
  - If issuer NIF = our company → **ClientInvoice** (revenue)
  - If recipient NIF = our company → **ProviderInvoice** (cost)
- For ProviderInvoice, the provider type is identified:
  - Shipping (Naviera)
  - Carrier (Transportista)
  - Inspection
  - Other
- Unknown parties are auto-created in the system
- The detected classification is shown to the user before saving

### HU-IA4 – Detailed Key Data Extraction
**As** a commercial agent  
**I want** the AI to extract all relevant data from the invoice  
**So that** I don't have to read and copy each field manually

**Acceptance Criteria:**
- The app must show a view with all extracted fields:
  - Main booking number
  - Ports (origin/destination)
  - Client or supplier
  - Container type
  - BL / references
  - Amounts by category (shipping, transport, inspection, insurance, others)
  - Taxes if applicable
  - Invoice date
- For carrier invoices, the AI must:
  - Detect each line associated with each booking
  - Group amounts correctly
  - Calculate total amounts per booking
- Extraction must work even if:
  - Lines are not aligned
  - Structure is not a standard table
  - There are multiple bookings in the same invoice

### HU-IA5 – Uncertainty Handling and Assisted Validation
**As** a commercial agent  
**I want** the AI to indicate when it's unsure about data or can't extract it  
**So that** I can review it manually before saving

**Acceptance Criteria:**
- If Claude Sonnet 4.5 cannot determine a field:
  - Marks it as "not found" or "ambiguous"
- User can manually edit fields before saving to the database
- The app must record in history which values were manually edited

### HU-IA6 – Model Error Handling
**As** a commercial agent  
**I want** to understand if there was a problem processing the invoice  
**So that** I can take manual action or retry processing

**Acceptance Criteria:**
- If the call to Claude Sonnet 4.5 fails (network, token, or timeout), the app:
  - Shows a clear message: "Could not process with AI"
  - Moves the document to the "With error" section
- User can click "Retry with AI"
- The system records the AI error in the database

### HU-IA7 – Reprocess an Already Processed Document
**As** a commercial agent  
**I want** to reprocess an invoice with Claude Sonnet 4.5 when there's a model improvement or prompt adjustment  
**So that** I can correct previously poorly extracted data

**Acceptance Criteria:**
- "Reprocess with AI" button available on processed invoices
- Reprocessing must:
  - Re-send the PDF to Sonnet 4.5
  - Replace old data
  - Record the new processing date

### HU-IA8 – Structured Preview (JSON) of Result
**As** a commercial agent  
**I want** to clearly see the data the AI has understood  
**So that** I can validate before saving to the database

**Acceptance Criteria:**
- After processing with AI, the app shows:
  - An editable fields panel (human side)
  - And the raw JSON returned by the model (technical side)
- User can toggle between "simple" and "advanced" view

---

## EPIC 4 – Booking Management & Commission Calculation

### HU4.1 – View Bookings List
**As** a commercial agent  
**I want** to see a list of all bookings with their financial status  
**So that** I can track my commissions

**Acceptance Criteria:**
- List shows: Booking ID, Client, POL/POD, Revenue, Costs, Margin, Commission, Status
- Filter by client, date range, status (Pending/Complete)
- Sort by date, margin, or commission

### HU4.2 – View Booking Detail with Commission
**As** a commercial agent  
**I want** to see the complete financial breakdown of a booking  
**So that** I understand my commission calculation

**Acceptance Criteria:**
- Shows all revenue charges (from client invoices)
- Shows all cost charges (from provider invoices) grouped by provider type
- Displays:
  - Total Revenue
  - Total Costs (with breakdown: Shipping, Carrier, Inspection, Other)
  - Margin (Revenue - Costs)
  - Commission Rate (from company settings)
  - **Agent Commission** (50% of Margin)
- Links to source invoice PDFs

### HU4.3 – Incremental Invoice Attribution to Bookings
**As** a commercial agent  
**I want** invoices that arrive on different days to accumulate into the same booking  
**So that** the commission is calculated correctly when all invoices are received

**Acceptance Criteria:**
- When processing an invoice, the system finds or creates the booking by ID
- Charges are added to existing booking (not replaced)
- Margin and commission are recalculated after each invoice
- Booking status remains PENDING until manually marked COMPLETE

### HU4.4 – Mark Booking as Complete
**As** a commercial agent  
**I want** to mark a booking as complete when all invoices have been received  
**So that** I know the commission is final

**Acceptance Criteria:**
- "Mark as Complete" button on booking detail
- Status changes from PENDING → COMPLETE
- Commission is considered final (but still editable if needed)
- Option to revert to PENDING if more invoices arrive

### HU4.5 – Commission Report
**As** a commercial agent  
**I want** to generate a commission report for a date range  
**So that** I can track my earnings and report to the company

**Acceptance Criteria:**
- Filter by date range and status (Pending/Complete)
- Shows: Booking ID, Client, Revenue, Costs, Margin, Commission
- Totals at the bottom
- Export to Excel

---

## EPIC 5 – Company & Agent Configuration

### HU5.1 – Configure Company Information
**As** a commercial agent  
**I want** to configure my company information  
**So that** the system can identify our invoices and calculate commissions

**Acceptance Criteria:**
- Configuration screen with:
  - Company name
  - NIF (used for invoice classification)
  - Address, contact info
  - Agent commission rate (default 50%)
- Company NIF is required for invoice processing to work

### HU5.2 – Configure Agent Profile
**As** a commercial agent  
**I want** to configure my profile  
**So that** my information is associated with the application

**Acceptance Criteria:**
- Profile screen with: Name, email, phone

---

## EPIC 6 – Data Storage (SQLite)

### HU6.1 – Store All Information in Local Database
**As** the system  
**I want** to store bookings, invoices, and parties in SQLite  
**So that** I maintain a complete and reliable record

**Acceptance Criteria:**
- Bookings table with charges stored as JSON
- Separate tables for client_invoices and provider_invoices
- Documents table for PDF tracking (pending, processed, error)
- Separate tables for clients and providers
- Company table (singleton) for our company info
- Agent table (singleton) for agent profile
- Settings table for API keys and preferences
- Duplicate documents not allowed (detection by PDF hash)

### HU6.2 – Search and Filter Data in the App
**As** a commercial agent  
**I want** to query information directly in the app  
**So that** I don't depend on external spreadsheets

**Acceptance Criteria:**
- Search bookings by: ID, client, date range, status
- Search invoices by: number, client/provider, date range

---

## EPIC 7 – On-Demand Excel Report Generation

### HU7.1 – Generate Excel Report from Database
**As** a commercial agent  
**I want** to generate an Excel with filtered data  
**So that** I can prepare reports or send them to Finance

**Acceptance Criteria:**
- Filters: Start/end date, client, booking, invoice type
- Generates a completely new .xlsx file
- File is saved to iCloud Drive or user-specified path

### HU7.2 – Specific Export by Booking or Client
**As** a commercial agent  
**I want** to export details of a specific booking  
**So that** I can analyze or share associated costs

**Acceptance Criteria:**
- "Export this booking" button in the detail view
- Export includes: all charges, revenue, costs, margin, commission
