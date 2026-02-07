"""Tests for invoice, document, party, and configuration entities."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from backend.domain.entities import (
    Agent,
    Client,
    ClientInvoice,
    Company,
    Document,
    Provider,
    ProviderInvoice,
    Settings,
)
from backend.domain.entities.party import normalize_nif
from backend.domain.enums import (
    ChargeCategory,
    DocumentType,
    ProcessingStatus,
    ProviderType,
)
from backend.domain.value_objects import (
    BookingCharge,
    ErrorInfo,
    FileHash,
    Money,
)


class TestNormalizeNif:
    """Tests for NIF normalization function."""

    def test_normalize_removes_spaces(self) -> None:
        """Test that normalization removes spaces."""
        assert normalize_nif("A 12 345 678") == "A12345678"

    def test_normalize_removes_dashes(self) -> None:
        """Test that normalization removes dashes."""
        assert normalize_nif("A-12-345-678") == "A12345678"

    def test_normalize_removes_dots(self) -> None:
        """Test that normalization removes dots."""
        assert normalize_nif("A.12.345.678") == "A12345678"

    def test_normalize_uppercase(self) -> None:
        """Test that normalization converts to uppercase."""
        assert normalize_nif("a12345678") == "A12345678"

    def test_normalize_combined(self) -> None:
        """Test normalization with mixed characters."""
        assert normalize_nif("a-12.345 678") == "A12345678"


class TestClientInvoice:
    """Tests for ClientInvoice entity."""

    def test_create_client_invoice(self) -> None:
        """Test creating a client invoice."""
        client_id = uuid4()
        invoice = ClientInvoice.create(
            invoice_number="INV-001",
            client_id=client_id,
            invoice_date=date(2024, 1, 15),
            bl_reference="BL-001",
            total_amount=Money.from_float(1210.00),
            tax_amount=Money.from_float(210.00),
        )
        assert invoice.invoice_number == "INV-001"
        assert invoice.client_id == client_id
        assert invoice.invoice_date == date(2024, 1, 15)
        assert invoice.bl_reference == "BL-001"
        assert invoice.total_amount == Money.from_float(1210.00)
        assert invoice.tax_amount == Money.from_float(210.00)
        assert invoice.charges == []
        assert invoice.id is not None

    def test_client_invoice_net_amount(self) -> None:
        """Test net amount calculation."""
        client_id = uuid4()
        invoice = ClientInvoice.create(
            invoice_number="INV-001",
            client_id=client_id,
            invoice_date=date(2024, 1, 15),
            bl_reference="BL-001",
            total_amount=Money.from_float(1210.00),
            tax_amount=Money.from_float(210.00),
        )
        assert invoice.net_amount == Money.from_float(1000.00)

    def test_client_invoice_add_charge(self) -> None:
        """Test adding charges to client invoice."""
        client_id = uuid4()
        invoice = ClientInvoice.create(
            invoice_number="INV-001",
            client_id=client_id,
            invoice_date=date(2024, 1, 15),
            bl_reference="BL-001",
            total_amount=Money.from_float(1210.00),
            tax_amount=Money.from_float(210.00),
        )
        charge = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice.id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Freight",
            amount=Money.from_float(1000.00),
        )
        invoice.add_charge(charge)
        assert len(invoice.charges) == 1
        assert invoice.charges[0] == charge


class TestProviderInvoice:
    """Tests for ProviderInvoice entity."""

    def test_create_provider_invoice(self) -> None:
        """Test creating a provider invoice."""
        provider_id = uuid4()
        invoice = ProviderInvoice.create(
            invoice_number="PROV-001",
            provider_id=provider_id,
            provider_type=ProviderType.SHIPPING,
            invoice_date=date(2024, 1, 15),
            bl_references=["BL-001"],
            total_amount=Money.from_float(1210.00),
            tax_amount=Money.from_float(210.00),
        )
        assert invoice.invoice_number == "PROV-001"
        assert invoice.provider_id == provider_id
        assert invoice.provider_type == ProviderType.SHIPPING
        assert invoice.bl_references == ["BL-001"]
        assert invoice.charges == []

    def test_provider_invoice_multi_booking(self) -> None:
        """Test provider invoice with multiple bookings."""
        provider_id = uuid4()
        invoice = ProviderInvoice.create(
            invoice_number="PROV-001",
            provider_id=provider_id,
            provider_type=ProviderType.SHIPPING,
            invoice_date=date(2024, 1, 15),
            bl_references=["BL-001", "BL-002"],
            total_amount=Money.from_float(2420.00),
            tax_amount=Money.from_float(420.00),
        )
        assert invoice.is_multi_booking
        assert len(invoice.bl_references) == 2

    def test_provider_invoice_add_charge(self) -> None:
        """Test adding charges to provider invoice."""
        provider_id = uuid4()
        invoice = ProviderInvoice.create(
            invoice_number="PROV-001",
            provider_id=provider_id,
            provider_type=ProviderType.SHIPPING,
            invoice_date=date(2024, 1, 15),
            bl_references=["BL-001"],
            total_amount=Money.from_float(968.00),
            tax_amount=Money.from_float(168.00),
        )
        charge = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice.id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container="CONT001",
            description="Shipping Cost",
            amount=Money.from_float(800.00),
        )
        invoice.add_charge(charge)
        assert len(invoice.charges) == 1

    def test_provider_invoice_get_charges_for_booking(self) -> None:
        """Test getting charges for specific booking."""
        provider_id = uuid4()
        invoice = ProviderInvoice.create(
            invoice_number="PROV-001",
            provider_id=provider_id,
            provider_type=ProviderType.SHIPPING,
            invoice_date=date(2024, 1, 15),
            bl_references=["BL-001", "BL-002"],
            total_amount=Money.from_float(1936.00),
            tax_amount=Money.from_float(336.00),
        )
        charge1 = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice.id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Charge for BL-001",
            amount=Money.from_float(800.00),
        )
        charge2 = BookingCharge(
            booking_id="BL-002",
            invoice_id=invoice.id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Charge for BL-002",
            amount=Money.from_float(800.00),
        )
        invoice.add_charge(charge1)
        invoice.add_charge(charge2)

        bl001_charges = invoice.get_charges_for_booking("BL-001")
        assert len(bl001_charges) == 1
        assert bl001_charges[0] == charge1

        bl002_total = invoice.get_total_for_booking("BL-002")
        assert bl002_total == Money.from_float(800.00)


class TestDocument:
    """Tests for Document entity."""

    def test_create_document(self) -> None:
        """Test creating a document."""
        file_hash = FileHash.sha256("abc123")
        doc = Document.create(
            filename="invoice.pdf",
            file_hash=file_hash,
            storage_path="/uploads/invoice.pdf",
        )
        assert doc.filename == "invoice.pdf"
        assert doc.storage_path == "/uploads/invoice.pdf"
        assert doc.file_hash == file_hash
        assert doc.status == ProcessingStatus.PENDING
        assert doc.document_type is None

    def test_document_status_transitions(self) -> None:
        """Test document status transitions."""
        doc = Document.create(
            filename="invoice.pdf",
            file_hash=FileHash.sha256("abc123"),
        )
        assert doc.status == ProcessingStatus.PENDING
        assert doc.is_pending

        doc.start_processing()
        assert doc.status == ProcessingStatus.PROCESSING
        assert doc.is_processing

        doc.mark_processed(DocumentType.CLIENT_INVOICE)
        assert doc.status == ProcessingStatus.PROCESSED
        assert doc.is_processed
        assert doc.document_type == DocumentType.CLIENT_INVOICE
        assert doc.is_invoice

    def test_document_mark_error(self) -> None:
        """Test marking document as error."""
        doc = Document.create(
            filename="invoice.pdf",
            file_hash=FileHash.sha256("abc123"),
        )
        doc.start_processing()
        error_info = ErrorInfo.api_key_missing()
        doc.mark_error(error_info)
        assert doc.status == ProcessingStatus.ERROR
        assert doc.is_error
        assert doc.error_info == error_info

    def test_document_can_retry(self) -> None:
        """Test checking if document can be retried."""
        doc = Document.create(
            filename="invoice.pdf",
            file_hash=FileHash.sha256("abc123"),
        )
        doc.start_processing()
        # API timeout is retryable
        doc.mark_error(ErrorInfo.ai_timeout())
        assert doc.can_retry()

        # Duplicate document is not retryable
        doc.start_processing()  # Can retry from error
        doc.mark_error(ErrorInfo.duplicate_document())
        assert not doc.can_retry()

    def test_document_link_invoice(self) -> None:
        """Test linking document to invoice after processing."""
        doc = Document.create(
            filename="invoice.pdf",
            file_hash=FileHash.sha256("abc123"),
        )
        invoice_id = uuid4()
        doc.start_processing()
        doc.mark_processed(DocumentType.CLIENT_INVOICE, invoice_id=invoice_id)
        assert doc.invoice_id == invoice_id


class TestClient:
    """Tests for Client entity."""

    def test_create_client(self) -> None:
        """Test creating a client."""
        client = Client.create(nif="A12345678", name="Test Client")
        assert client.name == "Test Client"
        assert client.nif == "A12345678"
        assert client.id is not None

    def test_create_client_default_name(self) -> None:
        """Test creating client with default name."""
        client = Client.create(nif="A12345678")
        assert client.name == "Unknown Client"

    def test_client_nif_normalized(self) -> None:
        """Test that client NIF is normalized."""
        client = Client.create(nif="a-12.345 678", name="Test Client")
        assert client.nif == "A12345678"

    def test_client_empty_nif_raises(self) -> None:
        """Test that empty NIF raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Client.create(nif="", name="Test Client")

    def test_client_update_name(self) -> None:
        """Test updating client name."""
        client = Client.create(nif="A12345678", name="Test Client")
        client.update_name("Updated Client")
        assert client.name == "Updated Client"


class TestProvider:
    """Tests for Provider entity."""

    def test_create_provider(self) -> None:
        """Test creating a provider."""
        provider = Provider.create(
            nif="B87654321",
            provider_type=ProviderType.SHIPPING,
            name="Shipping Co",
        )
        assert provider.name == "Shipping Co"
        assert provider.nif == "B87654321"
        assert provider.provider_type == ProviderType.SHIPPING

    def test_provider_default_name(self) -> None:
        """Test provider with default name."""
        provider = Provider.create(nif="B87654321")
        assert provider.name == "Unknown Provider"
        assert provider.provider_type == ProviderType.OTHER

    def test_provider_nif_normalized(self) -> None:
        """Test that provider NIF is normalized."""
        provider = Provider.create(
            nif="b-87.654 321",
            provider_type=ProviderType.SHIPPING,
        )
        assert provider.nif == "B87654321"

    def test_provider_empty_nif_raises(self) -> None:
        """Test that empty NIF raises error."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Provider.create(nif="")

    def test_provider_update_type(self) -> None:
        """Test updating provider type."""
        provider = Provider.create(nif="B87654321", provider_type=ProviderType.OTHER)
        provider.update_type(ProviderType.SHIPPING)
        assert provider.provider_type == ProviderType.SHIPPING


class TestCompany:
    """Tests for Company configuration entity."""

    def test_create_company(self) -> None:
        """Test creating a company."""
        company = Company.create(
            name="My Company",
            nif="A12345678",
        )
        assert company.name == "My Company"
        assert company.nif == "A12345678"
        assert company.agent_commission_rate == Decimal("0.50")

    def test_company_nif_normalized(self) -> None:
        """Test that company NIF is normalized."""
        company = Company.create(
            name="My Company",
            nif="a-12.345 678",
        )
        assert company.nif == "A12345678"

    def test_company_is_configured(self) -> None:
        """Test company configuration check."""
        company_not_configured = Company.create()
        assert not company_not_configured.is_configured

        company_configured = Company.create(name="My Co", nif="A12345678")
        assert company_configured.is_configured

    def test_company_update(self) -> None:
        """Test updating company info."""
        company = Company.create(name="My Company", nif="A12345678")
        company.update(name="Updated Company", commission_rate=Decimal("0.40"))
        assert company.name == "Updated Company"
        assert company.agent_commission_rate == Decimal("0.40")


class TestAgent:
    """Tests for Agent configuration entity."""

    def test_create_agent(self) -> None:
        """Test creating an agent."""
        agent = Agent.create(name="John Doe", email="john@example.com")
        assert agent.name == "John Doe"
        assert agent.email == "john@example.com"

    def test_create_agent_with_phone(self) -> None:
        """Test creating agent with phone."""
        agent = Agent.create(
            name="John Doe",
            email="john@example.com",
            phone="+34 666 123 456",
        )
        assert agent.phone == "+34 666 123 456"

    def test_agent_update(self) -> None:
        """Test updating agent info."""
        agent = Agent.create(name="John Doe", email="john@example.com")
        agent.update(name="Jane Doe", email="jane@example.com")
        assert agent.name == "Jane Doe"
        assert agent.email == "jane@example.com"


class TestSettings:
    """Tests for Settings configuration entity."""

    def test_create_default_settings(self) -> None:
        """Test creating settings with defaults."""
        settings = Settings.create()
        assert settings.has_api_key is False
        assert settings.outlook_configured is False

    def test_settings_set_api_key(self) -> None:
        """Test setting API key."""
        settings = Settings.create()
        settings.set_api_key("sk-ant-test-key")
        assert settings.has_api_key
        assert settings.anthropic_api_key == "sk-ant-test-key"

    def test_settings_clear_api_key(self) -> None:
        """Test clearing API key."""
        settings = Settings.create()
        settings.set_api_key("sk-ant-test-key")
        settings.clear_api_key()
        assert not settings.has_api_key
        assert settings.anthropic_api_key == ""

    def test_settings_outlook_connection(self) -> None:
        """Test Outlook connection settings."""
        settings = Settings.create()
        settings.set_outlook_configured(True, refresh_token="token123")
        assert settings.outlook_configured
        assert settings.outlook_refresh_token == "token123"

        settings.disconnect_outlook()
        assert not settings.outlook_configured
        assert settings.outlook_refresh_token == ""

    def test_settings_extraction_prompt(self) -> None:
        """Test extraction prompt management."""
        settings = Settings.create()
        original_prompt = settings.extraction_prompt

        settings.update_extraction_prompt("Custom prompt")
        assert settings.extraction_prompt == "Custom prompt"

        settings.reset_extraction_prompt()
        assert settings.extraction_prompt == original_prompt
