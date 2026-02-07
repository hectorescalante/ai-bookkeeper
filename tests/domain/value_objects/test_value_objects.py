"""Tests for value objects."""

from datetime import datetime
from uuid import uuid4

from backend.domain.enums import ChargeCategory, ConfidenceLevel, ErrorType, ProviderType
from backend.domain.value_objects import (
    BookingCharge,
    ClientInfo,
    DocumentReference,
    EmailReference,
    ErrorInfo,
    ExtractionMetadata,
    FieldConfidence,
    FileHash,
    Money,
    Port,
)


class TestBookingCharge:
    """Tests for BookingCharge value object."""

    def test_create_revenue_charge(self) -> None:
        """Test creating a revenue charge (no provider_type)."""
        invoice_id = uuid4()
        charge = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Ocean Freight",
            amount=Money.from_float(1000.00),
        )
        assert charge.booking_id == "BL-001"
        assert charge.invoice_id == invoice_id
        assert charge.charge_category == ChargeCategory.FREIGHT
        assert charge.provider_type is None
        assert charge.amount == Money.from_float(1000.00)

    def test_create_cost_charge(self) -> None:
        """Test creating a cost charge (with provider_type)."""
        invoice_id = uuid4()
        charge = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container="CONT001",
            description="Shipping Cost",
            amount=Money.from_float(800.00),
        )
        assert charge.provider_type == ProviderType.SHIPPING
        assert charge.container == "CONT001"

    def test_is_revenue(self) -> None:
        """Test is_revenue method."""
        invoice_id = uuid4()
        revenue = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Revenue",
            amount=Money.from_float(100.00),
        )
        cost = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Cost",
            amount=Money.from_float(100.00),
        )
        assert revenue.is_revenue()
        assert not cost.is_revenue()

    def test_is_cost(self) -> None:
        """Test is_cost method."""
        invoice_id = uuid4()
        revenue = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Revenue",
            amount=Money.from_float(100.00),
        )
        cost = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Cost",
            amount=Money.from_float(100.00),
        )
        assert cost.is_cost()
        assert not revenue.is_cost()


class TestClientInfo:
    """Tests for ClientInfo value object."""

    def test_create_client_info(self) -> None:
        """Test creating ClientInfo."""
        client_id = uuid4()
        client = ClientInfo(client_id=client_id, name="Test Client", nif="A12345678")
        assert client.client_id == client_id
        assert client.name == "Test Client"
        assert client.nif == "A12345678"


class TestPort:
    """Tests for Port value object."""

    def test_create_port(self) -> None:
        """Test creating Port."""
        port = Port(code="ESVAL", name="Valencia")
        assert port.code == "ESVAL"
        assert port.name == "Valencia"

    def test_port_str(self) -> None:
        """Test Port string representation."""
        port = Port(code="ESVAL", name="Valencia")
        # Format is "CODE (Name)"
        assert str(port) == "ESVAL (Valencia)"

    def test_port_str_no_name(self) -> None:
        """Test Port string without name."""
        port = Port(code="ESVAL", name="")
        assert str(port) == "ESVAL"


class TestFileHash:
    """Tests for FileHash value object."""

    def test_create_sha256_hash(self) -> None:
        """Test creating SHA256 file hash."""
        file_hash = FileHash.sha256("abc123def456")
        assert file_hash.algorithm == "sha256"
        assert file_hash.value == "abc123def456"

    def test_hash_str(self) -> None:
        """Test FileHash string representation."""
        file_hash = FileHash.sha256("abc123def4567890123456789")
        # Format is "algorithm:first16chars..."
        assert str(file_hash) == "sha256:abc123def4567890..."


class TestEmailReference:
    """Tests for EmailReference value object."""

    def test_create_email_reference(self) -> None:
        """Test creating EmailReference."""
        received = datetime(2024, 1, 15, 10, 30, 0)
        ref = EmailReference(
            message_id="MSG123",
            subject="Invoice attached",
            sender="supplier@example.com",
            received_at=received,
        )
        assert ref.message_id == "MSG123"
        assert ref.subject == "Invoice attached"
        assert ref.sender == "supplier@example.com"
        assert ref.received_at == received


class TestDocumentReference:
    """Tests for DocumentReference value object."""

    def test_create_document_reference(self) -> None:
        """Test creating DocumentReference."""
        doc_id = uuid4()
        file_hash = FileHash.sha256("abc123")
        ref = DocumentReference(
            document_id=doc_id,
            filename="invoice.pdf",
            file_hash=file_hash,
        )
        assert ref.document_id == doc_id
        assert ref.filename == "invoice.pdf"
        assert ref.file_hash == file_hash


class TestExtractionMetadata:
    """Tests for ExtractionMetadata value object."""

    def test_create_extraction_metadata(self) -> None:
        """Test creating ExtractionMetadata."""
        meta = ExtractionMetadata(
            ai_model="claude-sonnet-4-5-20250514",
            overall_confidence=ConfidenceLevel.HIGH,
        )
        assert meta.ai_model == "claude-sonnet-4-5-20250514"
        assert meta.overall_confidence == ConfidenceLevel.HIGH

    def test_extraction_metadata_with_field_confidences(self) -> None:
        """Test ExtractionMetadata with field confidences."""
        field_confidences = (
            FieldConfidence(field_name="invoice_number", confidence=ConfidenceLevel.HIGH),
            FieldConfidence(field_name="total", confidence=ConfidenceLevel.MEDIUM),
        )
        meta = ExtractionMetadata(
            ai_model="claude-sonnet-4-5-20250514",
            overall_confidence=ConfidenceLevel.MEDIUM,
            field_confidences=field_confidences,
        )
        assert len(meta.field_confidences) == 2
        assert meta.get_confidence_for("invoice_number") == ConfidenceLevel.HIGH
        assert meta.get_confidence_for("total") == ConfidenceLevel.MEDIUM
        assert meta.get_confidence_for("unknown") is None

    def test_overall_confidence_percentage(self) -> None:
        """Test overall confidence as percentage."""
        meta = ExtractionMetadata(
            ai_model="claude-sonnet-4-5-20250514",
            overall_confidence=ConfidenceLevel.HIGH,
        )
        # HIGH = 100%, MEDIUM = 70%, LOW = 40%
        assert meta.overall_confidence_percentage == 100

    def test_manually_edited_fields(self) -> None:
        """Test tracking manually edited fields."""
        meta = ExtractionMetadata(
            ai_model="claude-sonnet-4-5-20250514",
            overall_confidence=ConfidenceLevel.HIGH,
            manually_edited_fields=("invoice_number", "total"),
        )
        assert meta.was_manually_edited("invoice_number")
        assert meta.was_manually_edited("total")
        assert not meta.was_manually_edited("issuer_nif")

    def test_calculate_overall_confidence(self) -> None:
        """Test calculating overall confidence from critical fields."""
        overall = ExtractionMetadata.calculate_overall_confidence(
            document_type_confidence=ConfidenceLevel.HIGH,
            invoice_number_confidence=ConfidenceLevel.HIGH,
            issuer_nif_confidence=ConfidenceLevel.MEDIUM,  # Lowest
            recipient_nif_confidence=ConfidenceLevel.HIGH,
            total_confidence=ConfidenceLevel.HIGH,
        )
        # Overall is minimum of all
        assert overall == ConfidenceLevel.MEDIUM


class TestFieldConfidence:
    """Tests for FieldConfidence value object."""

    def test_create_field_confidence(self) -> None:
        """Test creating FieldConfidence."""
        fc = FieldConfidence(
            field_name="invoice_number",
            confidence=ConfidenceLevel.HIGH,
        )
        assert fc.field_name == "invoice_number"
        assert fc.confidence == ConfidenceLevel.HIGH


class TestErrorInfo:
    """Tests for ErrorInfo value object."""

    def test_create_error_info(self) -> None:
        """Test creating ErrorInfo."""
        error = ErrorInfo(
            error_type=ErrorType.AI_TIMEOUT,
            error_message="AI processing timed out",
        )
        assert error.error_type == ErrorType.AI_TIMEOUT
        assert error.error_message == "AI processing timed out"

    def test_nif_not_configured_factory(self) -> None:
        """Test nif_not_configured factory method."""
        error = ErrorInfo.nif_not_configured()
        assert error.error_type == ErrorType.NIF_NOT_CONFIGURED
        assert "Configure company NIF" in error.error_message

    def test_api_key_missing_factory(self) -> None:
        """Test api_key_missing factory method."""
        error = ErrorInfo.api_key_missing()
        assert error.error_type == ErrorType.API_KEY_MISSING
        assert "Configure API key" in error.error_message

    def test_api_key_invalid_factory(self) -> None:
        """Test api_key_invalid factory method."""
        error = ErrorInfo.api_key_invalid()
        assert error.error_type == ErrorType.API_KEY_INVALID
        assert "invalid" in error.error_message

    def test_ai_timeout_factory(self) -> None:
        """Test ai_timeout factory method."""
        error = ErrorInfo.ai_timeout()
        assert error.error_type == ErrorType.AI_TIMEOUT
        assert "timed out" in error.error_message

    def test_ai_rate_limit_factory(self) -> None:
        """Test ai_rate_limit factory method."""
        error = ErrorInfo.ai_rate_limit(10)
        assert error.error_type == ErrorType.AI_RATE_LIMIT
        assert "10 minutes" in error.error_message

    def test_file_too_large_factory(self) -> None:
        """Test file_too_large factory method."""
        error = ErrorInfo.file_too_large(25.5, max_mb=20)
        assert error.error_type == ErrorType.FILE_TOO_LARGE
        assert "25.5MB" in error.error_message
        assert "20MB" in error.error_message

    def test_too_many_pages_factory(self) -> None:
        """Test too_many_pages factory method."""
        error = ErrorInfo.too_many_pages(100, max_pages=50)
        assert error.error_type == ErrorType.TOO_MANY_PAGES
        assert "100 pages" in error.error_message
        assert "50" in error.error_message

    def test_duplicate_document_factory(self) -> None:
        """Test duplicate_document factory method."""
        error = ErrorInfo.duplicate_document()
        assert error.error_type == ErrorType.DUPLICATE_DOCUMENT
        assert "already imported" in error.error_message

    def test_invalid_currency_factory(self) -> None:
        """Test invalid_currency factory method."""
        error = ErrorInfo.invalid_currency("USD")
        assert error.error_type == ErrorType.INVALID_CURRENCY
        assert "USD" in error.error_message
        assert "EUR" in error.error_message

    def test_error_is_retryable(self) -> None:
        """Test is_retryable property."""
        # Retryable errors
        assert ErrorInfo.ai_timeout().is_retryable
        assert ErrorInfo.ai_rate_limit().is_retryable

        # Non-retryable errors
        assert not ErrorInfo.duplicate_document().is_retryable
        assert not ErrorInfo.invalid_currency("USD").is_retryable
