# Project Plan

This plan outlines delivery phases, key milestones, and scope boundaries for AI Bookkeeper. It complements the user stories and architecture docs.

## Goals
- Deliver a reliable local desktop app that automates invoice ingestion, extraction, and commission reporting.
- Keep all data local (SQLite + iCloud storage) and require human confirmation before saving.
- Maintain hexagonal architecture and testability.

## Non-Goals
- Multi-user or hosted SaaS deployment
- Fully autonomous processing without user confirmation
- ERP integrations in the initial release

## Phase 0 — Foundations
**Objective:** Establish baseline architecture, tooling, and environment.

**Milestones**
- Repo structure aligned with hexagonal architecture
- Backend + frontend dev environment running
- Basic CI checks documented (tests, lint, typecheck)

**Deliverables**
- `docs/architecture.md`, `docs/application.md`, `docs/user-stories.md`
- Working dev setup scripts and commands

## Phase 1 — Document Intake
**Objective:** Bring invoices into the system and manage document lifecycle.

**Milestones**
- Outlook OAuth flow (connect/disconnect)
- Fetch emails + detect PDF attachments
- Create Document records (PENDING/PROCESSED/ERROR)
- Duplicate detection via file hash

**Deliverables**
- `FetchEmails` and `ManageDocuments` use cases
- Document list UI (Pending/Processed/Errors)

## Phase 2 — AI Extraction & Validation
**Objective:** Extract structured invoice data with human review.

**Milestones**
- Gemini 3 extraction (text + scanned PDFs)
- Extraction preview (editable fields + raw JSON)
- Validation rules and error handling (currency, missing fields)
- Manual correction tracking

**Deliverables**
- `ProcessInvoice` + `ReprocessInvoice` use cases
- Process Invoice modal UI

## Phase 3 — Booking & Commission Engine
**Objective:** Aggregate invoices into bookings and compute commissions.

**Milestones**
- Booking creation/update from invoices
- Incremental aggregation of charges
- Commission calculation and booking status (PENDING/COMPLETE)
- Multi-booking invoice allocation (tax distribution)

**Deliverables**
- Booking list + booking detail UI
- Domain services: classifier, validator, duplicate checker

## Phase 4 — Reporting & Export
**Objective:** Provide financial outputs and exports.

**Milestones**
- Commission report by date range
- Excel export (booking and custom reports)
- Export paths and iCloud storage

**Deliverables**
- Reports UI
- Report generation adapters

## Phase 5 — Quality & Release
**Objective:** Stabilize, validate, and package.

**Milestones**
- Test coverage targets met (domain/use case/adapters)
- Error handling + logging verified
- Tauri build + release packaging steps documented

**Deliverables**
- `docs/test-plan.md` alignment
- Release checklist in `docs/`

## Risks & Mitigations
- **AI extraction variability** → strict validation + manual edits
- **Outlook OAuth fragility** → robust reconnect flow
- **Scanned PDFs** → image conversion and page size limits
- **Data integrity** → domain invariants + repository tests

## Dependencies
- Gemini API key (Gemini 3 Pro)
- Microsoft Graph OAuth app registration
- iCloud Drive availability (with fallback)

## References
- `docs/user-stories.md`
- `docs/application.md`
- `docs/architecture.md`
- `docs/test-plan.md`
