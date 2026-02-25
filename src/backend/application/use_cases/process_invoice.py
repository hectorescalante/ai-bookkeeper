"""Use case for processing an invoice document with AI extraction.

Orchestrates:
1. Validate preconditions (API key, company NIF)
2. Load document from repository
3. Read PDF and extract text/images
4. Send to AI for extraction
5. Return extracted data for user preview
"""

import logging
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from backend.application.dtos.invoice_dtos import ProcessInvoiceRequest, ProcessInvoiceResponse
from backend.domain.entities.configuration import DEFAULT_EXTRACTION_PROMPT
from backend.domain.enums import DocumentType, ErrorType, ProcessingStatus
from backend.domain.value_objects import ErrorInfo
from backend.ports.output.ai_extractor import (
    AIAuthError,
    AIExtractionError,
    AIExtractor,
    AIRateLimitError,
    AITimeoutError,
    PDFContent,
)
from backend.ports.output.repositories import (
    CompanyRepository,
    DocumentRepository,
    SettingsRepository,
)

logger = logging.getLogger(__name__)

# Processing limits
MAX_FILE_SIZE_MB = 20
MAX_PAGES = 50
MIN_TEXT_LENGTH = 100  # Characters below which PDF is considered scanned


class ProcessInvoiceUseCase:
    """Process a document by extracting invoice data with AI.

    Returns extracted data for user preview/validation before saving.
    """

    def __init__(
        self,
        document_repo: DocumentRepository,
        settings_repo: SettingsRepository,
        company_repo: CompanyRepository,
        ai_extractor: AIExtractor,
    ) -> None:
        self.document_repo = document_repo
        self.settings_repo = settings_repo
        self.company_repo = company_repo
        self.ai_extractor = ai_extractor

    def execute(self, request: ProcessInvoiceRequest) -> ProcessInvoiceResponse:
        """Execute the process invoice use case.

        Args:
            request: Contains the document_id to process

        Returns:
            ProcessInvoiceResponse with extracted data for user preview

        Raises:
            ValueError: If preconditions are not met
        """
        # 1. Validate preconditions
        settings = self.settings_repo.get()
        if not settings or not settings.has_api_key:
            raise ValueError("API key not configured. Set Gemini API key in Settings.")

        company = self.company_repo.get()
        if not company or not company.is_configured:
            raise ValueError("Company NIF not configured. Set company NIF in Settings.")

        # 2. Load document
        document = self.document_repo.find_by_id(request.document_id)
        if document is None:
            raise ValueError(f"Document not found: {request.document_id}")

        allowed_statuses = {ProcessingStatus.PENDING, ProcessingStatus.ERROR}
        if request.allow_processed:
            allowed_statuses.add(ProcessingStatus.PROCESSED)

        if document.status not in allowed_statuses:
            raise ValueError(
                f"Document cannot be processed in {document.status.value} status"
            )

        # 3. Mark as processing
        document.start_processing(allow_reprocess=request.allow_processed)
        self.document_repo.update(document)

        try:
            # 4. Read PDF content
            pdf_content = self._read_pdf(document.storage_path, document.filename)

            # 5. Get extraction prompt
            extraction_prompt = settings.extraction_prompt or DEFAULT_EXTRACTION_PROMPT

            # 6. Send to AI
            result = self.ai_extractor.extract_invoice_data(
                pdf_content=pdf_content,
                company_nif=company.nif,
                extraction_prompt=extraction_prompt,
            )

            # 7. Build response for user preview
            invoice_data = result.invoice_data or {}
            issuer = invoice_data.get("issuer", {}) or {}
            recipient = invoice_data.get("recipient", {}) or {}
            totals = invoice_data.get("totals", {}) or {}

            # Determine overall confidence
            overall_confidence = self._calculate_overall_confidence(
                result.parsed_data, invoice_data
            )

            # Check currency
            currency_valid = invoice_data.get("currency_valid", True)
            currency_detected = invoice_data.get("currency_detected", "EUR")

            warnings: list[str] = []
            errors: list[str] = []

            if not currency_valid:
                errors.append(
                    f"Invoice currency is {currency_detected}. "
                    "Only EUR invoices are supported."
                )

            if result.document_type == DocumentType.OTHER.value:
                warnings.append(
                    "Document classified as OTHER (not an invoice). "
                    "You can override this classification."
                )

            return ProcessInvoiceResponse(
                document_id=document.id,
                document_type=result.document_type or "OTHER",
                document_type_confidence=result.document_type_confidence or "LOW",
                ai_model=result.model_used,
                raw_json=result.raw_json,
                invoice_number=invoice_data.get("invoice_number"),
                invoice_date=invoice_data.get("invoice_date"),
                issuer_name=issuer.get("name"),
                issuer_nif=issuer.get("nif"),
                recipient_name=recipient.get("name"),
                recipient_nif=recipient.get("nif"),
                provider_type=invoice_data.get("provider_type"),
                currency_valid=currency_valid,
                currency_detected=currency_detected,
                bl_references=invoice_data.get("bl_references", []),
                charges=invoice_data.get("charges", []),
                totals=totals,
                extraction_notes=result.extraction_notes,
                overall_confidence=overall_confidence,
                warnings=warnings,
                errors=errors,
            )

        except AIAuthError as err:
            document.mark_error(ErrorInfo.api_key_invalid())
            self.document_repo.update(document)
            raise ValueError(
                "Gemini API key is invalid. Update it in Settings."
            ) from err

        except AITimeoutError as err:
            document.mark_error(ErrorInfo.ai_timeout())
            self.document_repo.update(document)
            raise ValueError(
                "AI processing timed out. Please retry."
            ) from err

        except AIRateLimitError as e:
            document.mark_error(ErrorInfo.ai_rate_limit(e.retry_after_minutes))
            self.document_repo.update(document)
            raise ValueError(
                f"AI rate limit reached. Try again in {e.retry_after_minutes} minutes."
            ) from e

        except AIExtractionError as e:
            document.mark_error(
                ErrorInfo(
                    error_type=ErrorType.AI_TIMEOUT,  # Generic AI error
                    error_message=str(e),
                )
            )
            self.document_repo.update(document)
            raise ValueError(f"AI extraction failed: {e}") from e

    def _read_pdf(self, storage_path: str | None, filename: str) -> PDFContent:
        """Read PDF file and extract text/images.

        Args:
            storage_path: Path to the PDF file
            filename: Original filename

        Returns:
            PDFContent with text and/or image data

        Raises:
            ValueError: If file is too large or has too many pages
        """
        if not storage_path:
            raise ValueError("Document has no storage path")

        path = Path(storage_path)
        if not path.exists():
            raise ValueError(f"PDF file not found: {storage_path}")

        # Check file size
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(
                f"File too large: {file_size_mb:.1f}MB (max {MAX_FILE_SIZE_MB}MB)"
            )

        # Read PDF
        reader = PdfReader(str(path))
        page_count = len(reader.pages)

        if page_count > MAX_PAGES:
            raise ValueError(
                f"Too many pages: {page_count} (max {MAX_PAGES})"
            )

        # Extract text
        text_parts: list[str] = []
        for page in reader.pages:
            text = page.extract_text() or ""
            text_parts.append(text)

        full_text = "\n".join(text_parts)

        # Determine if scanned
        is_scanned = len(full_text.strip()) < MIN_TEXT_LENGTH
        # Extract embedded page images for scanned PDFs.
        page_images: list[bytes] = []
        if is_scanned:
            page_images = self._extract_page_images(reader)
            if not page_images:
                logger.warning(
                    "Scanned PDF detected but no embedded images were extracted",
                    extra={"document_filename": filename, "page_count": page_count},
                )

        return PDFContent(
            text_content=full_text,
            page_images=page_images,
            page_count=page_count,
            is_scanned=is_scanned,
            filename=filename,
        )

    def _extract_page_images(self, reader: PdfReader) -> list[bytes]:
        """Extract embedded image bytes from all PDF pages."""
        extracted_images: list[bytes] = []

        for page_index, page in enumerate(reader.pages):
            try:
                page_images = getattr(page, "images", [])
                for image in page_images:
                    image_bytes = self._extract_image_bytes(image)
                    if image_bytes:
                        extracted_images.append(image_bytes)
            except Exception as err:
                logger.warning(
                    "Failed to extract images from PDF page",
                    extra={"page_index": page_index, "error": str(err)},
                )

        return extracted_images

    @staticmethod
    def _extract_image_bytes(image: Any) -> bytes | None:
        """Return raw bytes for a pypdf image object when available."""
        image_data = getattr(image, "data", None)
        if isinstance(image_data, bytes) and image_data:
            return image_data
        return None

    def _calculate_overall_confidence(
        self,
        parsed_data: dict[str, Any],
        invoice_data: dict[str, Any],
    ) -> str:
        """Calculate overall confidence as minimum of critical fields."""
        confidence_order = {"high": 3, "medium": 2, "low": 1}

        confidences = [
            parsed_data.get("document_type_confidence", "low"),
            invoice_data.get("invoice_number_confidence", "low"),
        ]

        issuer = invoice_data.get("issuer", {}) or {}
        recipient = invoice_data.get("recipient", {}) or {}
        totals = invoice_data.get("totals", {}) or {}

        confidences.extend([
            issuer.get("nif_confidence", "low"),
            recipient.get("nif_confidence", "low"),
            totals.get("total_confidence", "low"),
        ])

        min_val = min(confidence_order.get(c, 1) for c in confidences)

        for level, val in confidence_order.items():
            if val == min_val:
                return level.upper()

        return "LOW"
