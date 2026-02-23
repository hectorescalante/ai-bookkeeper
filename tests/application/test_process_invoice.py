"""Tests for ProcessInvoice use case."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.application.dtos.invoice_dtos import ProcessInvoiceRequest
from backend.application.use_cases.process_invoice import ProcessInvoiceUseCase
from backend.domain.entities.configuration import Company, Settings
from backend.domain.entities.document import Document
from backend.domain.enums import ProcessingStatus
from backend.domain.value_objects import FileHash
from backend.ports.output.ai_extractor import (
    AIAuthError,
    AIRateLimitError,
    AITimeoutError,
    ExtractionResult,
)


def _make_settings(has_key: bool = True) -> Settings:
    """Create test settings."""
    settings = Settings.create()
    if has_key:
        settings.set_api_key("test-gemini-key")
    return settings


def _make_company(nif: str = "B12345678") -> Company:
    """Create test company."""
    return Company.create(name="Test Company", nif=nif)


def _make_document(storage_path: str | None = None) -> Document:
    """Create test document."""
    doc = Document.create(
        filename="invoice.pdf",
        file_hash=FileHash.sha256("abc123"),
        storage_path=storage_path,
    )
    return doc


def _make_extraction_result() -> ExtractionResult:
    """Create a mock extraction result."""
    parsed_data = {
        "document_type": "PROVIDER_INVOICE",
        "document_type_confidence": "high",
        "invoice": {
            "invoice_number": "INV-001",
            "invoice_number_confidence": "high",
            "invoice_date": "2024-01-15",
            "issuer": {
                "name": "Provider S.A.",
                "nif": "A99999999",
                "nif_confidence": "high",
            },
            "recipient": {
                "name": "Test Company",
                "nif": "B12345678",
                "nif_confidence": "high",
            },
            "provider_type": "SHIPPING",
            "provider_type_confidence": "high",
            "currency_valid": True,
            "currency_detected": "EUR",
            "bl_references": [
                {"bl_number": "BL-001", "bl_confidence": "high"}
            ],
            "charges": [
                {
                    "bl_reference": "BL-001",
                    "description": "Ocean Freight",
                    "container": None,
                    "category": "FREIGHT",
                    "amount": 1250.00,
                    "amount_confidence": "high",
                }
            ],
            "totals": {
                "subtotal": 1250.00,
                "tax_rate": 21,
                "tax_amount": 262.50,
                "total": 1512.50,
                "total_confidence": "high",
            },
        },
        "extraction_notes": None,
    }
    import json

    return ExtractionResult(
        raw_json=json.dumps(parsed_data),
        parsed_data=parsed_data,
        model_used="gemini-3-pro",
    )


def _create_dummy_pdf(path: str) -> None:
    """Create a minimal valid PDF file for testing."""
    # Minimal PDF structure
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << >> >>\nendobj\n"
        b"4 0 obj\n<< /Length 44 >>\nstream\n"
        b"BT /F1 12 Tf 100 700 Td (Invoice) Tj ET\n"
        b"endstream\nendobj\n"
        b"xref\n0 5\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000250 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n344\n%%EOF"
    )
    Path(path).write_bytes(pdf_content)


class TestProcessInvoiceUseCase:
    """Tests for ProcessInvoiceUseCase."""

    def test_process_invoice_success(self) -> None:
        """Test successful invoice processing."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            _create_dummy_pdf(f.name)
            doc = _make_document(storage_path=f.name)

        # Mock repositories
        doc_repo = MagicMock()
        doc_repo.find_by_id.return_value = doc

        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()

        company_repo = MagicMock()
        company_repo.get.return_value = _make_company()

        ai_extractor = MagicMock()
        ai_extractor.extract_invoice_data.return_value = _make_extraction_result()

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        request = ProcessInvoiceRequest(document_id=doc.id)
        result = use_case.execute(request)

        assert result.document_type == "PROVIDER_INVOICE"
        assert result.invoice_number == "INV-001"
        assert result.issuer_nif == "A99999999"
        assert result.recipient_nif == "B12345678"
        assert result.ai_model == "gemini-3-pro"
        assert result.currency_valid is True
        assert len(result.charges) == 1

        # Verify document was marked as processing
        doc_repo.update.assert_called()

    def test_process_invoice_no_api_key(self) -> None:
        """Test error when API key is not configured."""
        doc_repo = MagicMock()
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings(has_key=False)
        company_repo = MagicMock()
        ai_extractor = MagicMock()

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        with pytest.raises(ValueError, match="API key not configured"):
            use_case.execute(ProcessInvoiceRequest(document_id=uuid4()))

    def test_process_invoice_no_company_nif(self) -> None:
        """Test error when company NIF is not configured."""
        doc_repo = MagicMock()
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()
        company_repo = MagicMock()
        company_repo.get.return_value = Company.create()  # No NIF
        ai_extractor = MagicMock()

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        with pytest.raises(ValueError, match="Company NIF not configured"):
            use_case.execute(ProcessInvoiceRequest(document_id=uuid4()))

    def test_process_invoice_document_not_found(self) -> None:
        """Test error when document is not found."""
        doc_repo = MagicMock()
        doc_repo.find_by_id.return_value = None
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()
        company_repo = MagicMock()
        company_repo.get.return_value = _make_company()
        ai_extractor = MagicMock()

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        with pytest.raises(ValueError, match="Document not found"):
            use_case.execute(ProcessInvoiceRequest(document_id=uuid4()))

    def test_process_invoice_already_processed(self) -> None:
        """Test error when document is already processed."""
        doc = _make_document()
        doc.status = ProcessingStatus.PROCESSED

        doc_repo = MagicMock()
        doc_repo.find_by_id.return_value = doc
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()
        company_repo = MagicMock()
        company_repo.get.return_value = _make_company()
        ai_extractor = MagicMock()

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        with pytest.raises(ValueError, match="cannot be processed"):
            use_case.execute(ProcessInvoiceRequest(document_id=doc.id))

    def test_process_invoice_ai_timeout(self) -> None:
        """Test handling of AI timeout error."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            _create_dummy_pdf(f.name)
            doc = _make_document(storage_path=f.name)

        doc_repo = MagicMock()
        doc_repo.find_by_id.return_value = doc
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()
        company_repo = MagicMock()
        company_repo.get.return_value = _make_company()

        ai_extractor = MagicMock()
        ai_extractor.extract_invoice_data.side_effect = AITimeoutError("Timed out")

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        with pytest.raises(ValueError, match="timed out"):
            use_case.execute(ProcessInvoiceRequest(document_id=doc.id))

        # Document should be marked as error
        assert doc.status == ProcessingStatus.ERROR

    def test_process_invoice_ai_auth_error(self) -> None:
        """Test handling of AI auth error."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            _create_dummy_pdf(f.name)
            doc = _make_document(storage_path=f.name)

        doc_repo = MagicMock()
        doc_repo.find_by_id.return_value = doc
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()
        company_repo = MagicMock()
        company_repo.get.return_value = _make_company()

        ai_extractor = MagicMock()
        ai_extractor.extract_invoice_data.side_effect = AIAuthError("Invalid key")

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        with pytest.raises(ValueError, match="invalid"):
            use_case.execute(ProcessInvoiceRequest(document_id=doc.id))

        assert doc.status == ProcessingStatus.ERROR

    def test_process_invoice_ai_rate_limit(self) -> None:
        """Test handling of AI rate limit error."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            _create_dummy_pdf(f.name)
            doc = _make_document(storage_path=f.name)

        doc_repo = MagicMock()
        doc_repo.find_by_id.return_value = doc
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()
        company_repo = MagicMock()
        company_repo.get.return_value = _make_company()

        ai_extractor = MagicMock()
        ai_extractor.extract_invoice_data.side_effect = AIRateLimitError(
            retry_after_minutes=10
        )

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        with pytest.raises(ValueError, match="rate limit"):
            use_case.execute(ProcessInvoiceRequest(document_id=doc.id))

        assert doc.status == ProcessingStatus.ERROR

    def test_process_invoice_non_eur_currency(self) -> None:
        """Test handling of non-EUR currency detection."""
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            _create_dummy_pdf(f.name)
            doc = _make_document(storage_path=f.name)

        # Extraction result with non-EUR currency
        result = _make_extraction_result()
        result.parsed_data["invoice"]["currency_valid"] = False
        result.parsed_data["invoice"]["currency_detected"] = "USD"

        doc_repo = MagicMock()
        doc_repo.find_by_id.return_value = doc
        settings_repo = MagicMock()
        settings_repo.get.return_value = _make_settings()
        company_repo = MagicMock()
        company_repo.get.return_value = _make_company()

        ai_extractor = MagicMock()
        ai_extractor.extract_invoice_data.return_value = result

        use_case = ProcessInvoiceUseCase(
            document_repo=doc_repo,
            settings_repo=settings_repo,
            company_repo=company_repo,
            ai_extractor=ai_extractor,
        )

        response = use_case.execute(ProcessInvoiceRequest(document_id=doc.id))

        assert response.currency_valid is False
        assert response.currency_detected == "USD"
        assert any("EUR" in e for e in response.errors)
