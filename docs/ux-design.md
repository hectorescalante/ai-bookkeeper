# UX Design

This document defines the user experience: navigation, screens, flows, and UI patterns.

## Navigation Structure

```
┌─────────────────────────────────────────────────────────────┐
│  AI Bookkeeper                                             │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│  📄 Documents│           Main Content Area                  │
│              │                                              │
│  📦 Bookings │                                              │
│              │                                              │
│  📊 Reports  │                                              │
│              │                                              │
│  ⚙️ Settings │                                              │
│              │                                              │
└──────────────┴──────────────────────────────────────────────┘
```

**Sidebar Navigation:**
- Documents (default view)
- Bookings
- Reports
- Settings

---

## Screens

### 1. Documents

Three tabs showing document processing status.

```
┌─ Documents ─────────────────────────────────────────────────┐
│                                                             │
│  [🔄 Fetch Emails]                          [Filter ▼]      │
│                                                             │
│  ┌─────────┬───────────┬─────────┐                         │
│  │ Pending │ Processed │ Errors  │                         │
│  │  (12)   │   (156)   │   (3)   │                         │
│  └─────────┴───────────┴─────────┘                         │
│                                                             │
│  ☑️ Select All                              [Process Selected]│
│  ┌─────────────────────────────────────────────────────────┐│
│  │ ☑️ invoice_001.pdf  │ sender@email.com │ Jan 10, 2024  ││
│  │ ☑️ invoice_002.pdf  │ carrier@ship.com │ Jan 10, 2024  ││
│  │ ☐ packing_list.pdf │ logistics@co.com │ Jan 09, 2024  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

**Pending Tab:**
- Checkbox for multi-select
- Filename, sender, date received
- Email indicator: Documents from the same email show a link icon 🔗 with tooltip "From same email as [filename]"
- [📄 View PDF] button to preview before processing
- "Process Selected" button
- "Fetch Emails" button to check for new

**Processed Tab:**
- Document type (Client/Provider/Other)
- Linked booking
- Invoice amount
- Date processed
- [📄 View PDF] opens file in external system viewer (macOS Preview)
- Click row to view invoice details

**Errors Tab:**
- Error message
- [📄 View PDF] button to check source document
- "Retry" button per document
- "View Details" to see full error

---

### 2. Process Invoice (Modal/Dialog)

Shown after AI extraction, before saving.

```
┌─ Process Invoice ───────────────────────────────────────────┐
│                                                             │
│  Document: invoice_001.pdf              [View PDF]          │
│  Type: Provider Invoice (Shipping)      ✓ Detected          │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Invoice Number:  [INV-2024-0123    ]                       │
│  Provider:        [Mediterranean Lines ▼]  NIF: B11111111   │
│  Invoice Date:    [📅 2024-01-10    ]                       │
│                                                             │
│  BL Reference:    [BL-2024-001234   ]  → Booking: NEW       │
│                                                             │
│  ─── Charges ───────────────────────────────────────────    │
│  │ Description          │ Container  │ Amount    │          │
│  │ Ocean freight        │ MSCU123456 │ €1,250.00 │ [Edit]   │
│  │ Port handling        │ MSCU123456 │ €350.00   │ [Edit]   │
│  │ Documentation        │ —          │ €75.00    │ [Edit]   │
│  │                                   [+ Add Charge]         │
│                                                             │
│  Total: €1,675.00                    Tax: €351.75           │
│                                                             │
│  ─────────────────────────────────────────────────────────  │
│  ⚠️ Confidence: 87% — Review highlighted fields             │
│                                                             │
│  [Cancel]                           [Save & Attribute]      │
│                                                             │
│  ┌─ Advanced ─────────────────────────────────────────────┐ │
│  │ { "raw_json": "..." }                         [Toggle] │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- All fields editable
- Low-confidence fields highlighted (yellow background)
- Provider dropdown with auto-complete
- BL Reference shows if booking exists or will be created
- Charges table with inline edit
- "View PDF" opens document in side panel
- Advanced toggle shows raw AI JSON

---

### 3. Bookings

List of all bookings with financial summary.

```
┌─ Bookings ──────────────────────────────────────────────────────────┐
│                                                                  │
│  [Status ▼]  [Client ▼]  [📅 Date Range]  [🔍 Search]            │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────────┐│
│  │ ID           │ Client   │ Docs │ Revenue │ Costs  │ Margin   ││
│  ├───────────────────────────────────────────────────────────────┤│
│  │ BL-2024-1234 │ Acme Inc │  3   │ €6,500  │ €5,500 │ €1,000 🟢││
│  │ BL-2024-1233 │ MegaCorp │  2   │ €4,200  │ €3,800 │ €400   🟡││
│  │ BL-2024-1232 │ Acme Inc │  1   │ €0      │ €2,100 │ -€2,100🟡││
│  └───────────────────────────────────────────────────────────────┘│
│                                                                  │
│  🟢 Complete (45)   🟡 Pending (12)                              │
│                                                                  │
│  Showing 1-20 of 57                         [< Prev] [Next >]    │
└──────────────────────────────────────────────────────────────────┘
```

**Features:**
- Status color: 🟢 Complete, 🟡 Pending (status, not margin)
- Docs column: number of linked invoices/documents
- Margin column shows financial result (negative allowed)
- Sortable columns
- Filter by status, client, date range
- Search by booking ID
- Click row to view detail

---

### 4. Booking Detail

Full breakdown of a single booking.

```
┌─ Booking: BL-2024-001234 ───────────────────────────────┐
│                                                             │
│  Client: Acme Mining Corp            Status: [🟡 Pending ▼] │
│  POL: Shanghai (CNSHA)               POD: Valencia (ESVLC)  │
│  Vessel: MSC Oscar                   Created: Jan 5, 2024   │
│                                                             │
│  ═════════════════════════════════════════════════════════════│
│                                                             │
│  💰 REVENUE (1 invoice)                          [▼ Expand] │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Invoice      │ Date       │ Amount   │ [PDF]           ││
│  │ INV-2024-100 │ Jan 10     │ €6,500   │ 📄              ││
│  └─────────────────────────────────────────────────────────┘│
│  Total Revenue: €6,500                                      │
│                                                             │
│  📦 COSTS (4 invoices)                          [▼ Expand] │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ Provider         │ Type     │ Invoice  │ Amount │ [PDF]││
│  │ Mediterranean    │ Shipping │ SHP-1234 │ €2,500 │ 📄   ││
│  │ Express Trans    │ Carrier  │ TRN-5678 │ €1,800 │ 📄   ││
│  │ Express Trans    │ Carrier  │ TRN-5679 │ €1,200 │ 📄   ││
│  │ SGS Inspection   │ Inspect  │ INS-0012 │ €450   │ 📄   ││
│  │                              Showing 4 of 4              ││
│  └─────────────────────────────────────────────────────────┘│
│  Total Costs: €5,950                                        │
│  ├── Shipping:   €2,500 (1 invoice)                         │
│  ├── Carrier:    €3,000 (2 invoices)                        │
│  ├── Inspection: €450   (1 invoice)                         │
│  └── Other:      €0                                         │
│                                                             │
│  ═════════════════════════════════════════════════════════════│
│                                                             │
│  MARGIN:      €550   (8.5%)                                 │
│  COMMISSION:  €275   (50% of margin)                        │
│                                                             │
│  [Edit Booking]  [Export to Excel]  [Mark as Complete ✓]    │
└─────────────────────────────────────────────────────────────┘
```

**Features:**
- Revenue section with invoice count, collapsible, [📄 View PDF] per row
- Costs section with invoice count, collapsible, grouped by provider type
- Scrollable invoice tables when many invoices
- Cost breakdown shows invoice count per category
- Every invoice row has direct link to source PDF
- Status dropdown (Pending/Complete)
- Edit, Export, Complete actions

**Multi-Booking Invoice Display:**
When an invoice spans multiple bookings, the booking detail shows:
- Only charges attributed to THIS booking (not the full invoice)
- "Amount" column shows the sum of charges for this booking
- Tooltip on amount: "This booking: €600 of €1,000 invoice total"
- [📄 View PDF] opens the full original invoice

---

### 5. Reports

Generate and export reports.

```
┌─ Reports ───────────────────────────────────────────────────┐
│                                                             │
│  ┌─ Commission Report ────────────────────────────────────┐ │
│  │                                                         │ │
│  │  Date Range: [📅 Jan 1, 2024] to [📅 Jan 31, 2024]     │ │
│  │  Status:     [Complete only ▼]                         │ │
│  │                                                         │ │
│  │  Preview:                                               │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │ 15 bookings │ €45,200 revenue │ €12,500 commission│  │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  │                                                         │ │
│  │  [Generate Excel]                                       │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Custom Export ────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  Data:   [Bookings ▼]                                  │ │
│  │  Filter: [All ▼]  Client: [Any ▼]                      │ │
│  │  Date:   [📅 From] to [📅 To]                          │ │
│  │                                                         │ │
│  │  [Export to Excel]                                      │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

### 6. Settings

Configuration screens.

```
┌─ Settings ──────────────────────────────────────────────────┐
│                                                             │
│  ┌─ Company ──────────────────────────────────────────┐ │
│  │  Company Name:  [Your Company S.L.        ]            │ │
│  │  NIF:           [B12345678                ]  ⚠️ Required│ │
│  │  Address:       [123 Main Street, Valencia ]           │ │
│  │  Commission:    [50    ] %                             │ │
│  │                                          [Save]        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Agent Profile ────────────────────────────────────────┐ │
│  │  Name:   [Your Name                       ]            │ │
│  │  Email:  [agent@company.com               ]            │ │
│  │  Phone:  [+34 600 000 000                 ]            │ │
│  │                                          [Save]        │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Integrations ─────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  Gemini API                                         │ │
│  │  [••••••••••••••••••••••••••    ] [Test] ✅ Connected  │ │
│  │                                                         │ │
│  │  Outlook                                                │ │
│  │  [Connect Account]               ❌ Not connected       │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ AI Prompt ────────────────────────────────────────────┐ │
│  │                                                         │ │
│  │  Extraction Prompt Template:                            │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │ You are an invoice data extraction assistant... │   │ │
│  │  │ Extract the following fields from the PDF:      │   │ │
│  │  │ ...                                             │   │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  │                                                         │ │
│  │  [Reset to Default]                         [Save]      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌─ Help ─────────────────────────────────────────────────┐ │
│  │  [Export Diagnostics] [Open file location] [Share by email] │ │
│  │  Latest bundle: /.../diagnostics-YYYYMMDD-HHMMSS.zip   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**Help Section (Diagnostics):**
- **Export Diagnostics** creates a zip bundle for support.
- **Open file location** reveals the generated zip in Finder.
- **Share by email** opens a prefilled email draft.
- A note reminds users that the zip must be attached manually.

---

## User Flows

### Flow 1: Process New Invoices

```
Documents (Pending)
    │
    ├── Click "Fetch Emails"
    │   └── Toast: "Found 5 new documents"
    │
    ├── Select documents (checkbox)
    │
    └── Click "Process Selected"
        │
        └── For each document:
            │
            ├── [Processing...] spinner
            │
            ├── AI extracts data
            │
            └── Process Invoice Modal opens
                │
                ├── Review/edit fields
                │
                ├── Click "Save & Attribute"
                │   ├── Toast: "Invoice saved"
                │   ├── Booking created/updated
                │   └── Next document...
                │
                └── Or "Cancel" → document stays pending
```

### Flow 2: Review Booking & Mark Complete

```
Bookings
    │
    ├── Filter by status: Pending
    │
    └── Click booking row
        │
        └── Booking Detail
            │
            ├── Review charges and margin
            │
            ├── Verify all invoices received
            │
            └── Click "Mark as Complete"
                │
                └── Status changes to 🟢 Complete
```

### Flow 3: Generate Commission Report

```
Reports
    │
    ├── Select date range
    │
    ├── Set status filter (Complete)
    │
    ├── Preview shows summary
    │
    └── Click "Generate Excel"
        │
        ├── File saved to iCloud
        │
        └── Toast: "Report saved to ~/iCloud/AIBookkeeper/reports/"
```

### Flow 4: Export Diagnostics for Support

```
Settings → Help
    │
    ├── Click "Export Diagnostics"
    │   └── Toast: "Diagnostics exported"
    │
    ├── Review generated bundle path
    │
    ├── Click "Open file location" (Finder reveals zip)
    │
    └── Click "Share by email"
        │
        └── Email draft opens (user attaches zip manually)
```

---

## UI Patterns

### Toast Notifications
```
┌──────────────────────────────────────┐
│ ✅ Invoice saved to booking BL-1234  │  [×]
└──────────────────────────────────────┘
```
- Success: Green
- Warning: Yellow  
- Error: Red
- Auto-dismiss after 5 seconds

### Confirmation Dialogs
```
┌─ Confirm ────────────────────────────┐
│                                      │
│  Mark booking as complete?           │
│                                      │
│  Commission will be finalized.       │
│                                      │
│        [Cancel]  [Confirm]           │
└──────────────────────────────────────┘
```

### Loading States
- Button: Show spinner, disable button
- Table: Skeleton rows
- Full page: Centered spinner with message

### Empty States
```
┌──────────────────────────────────────┐
│                                      │
│         📄                           │
│    No pending documents              │
│                                      │
│    Click "Fetch Emails" to check     │
│    for new invoices.                 │
│                                      │
│    [Fetch Emails]                    │
└──────────────────────────────────────┘
```

### Form Validation
- Inline error messages below fields
- Red border on invalid fields
- Disable submit until valid

---

## Design Guidelines

### Colors
- Primary: Blue (#3B82F6)
- Success: Green (#10B981)
- Warning: Yellow (#F59E0B)
- Error: Red (#EF4444)
- Neutral: Gray scale

### Typography
- Headings: Semi-bold
- Body: Regular
- Monospace: Invoice numbers, amounts

### Spacing
- Consistent 8px grid
- Card padding: 16px
- Section gaps: 24px

### Responsive
- Fixed sidebar (collapsible on small screens)
- Main content scrolls
- Modals centered with max-width

---

## PrimeVue Components

| Pattern | Component |
|---------|-----------|
| Navigation | `Menu` or `PanelMenu` |
| Data tables | `DataTable` with sorting, filtering |
| Forms | `InputText`, `Dropdown`, `Calendar` |
| Buttons | `Button` with icons |
| Modals | `Dialog` |
| Tabs | `TabView` |
| Toasts | `Toast` |
| Loading | `ProgressSpinner` |
| Cards | `Card` |
| Confirmations | `ConfirmDialog` |
