"""Tests for Booking entity."""

from decimal import Decimal
from uuid import uuid4

import pytest

from backend.domain.entities import Booking
from backend.domain.enums import BookingStatus, ChargeCategory, ProviderType
from backend.domain.value_objects import BookingCharge, ClientInfo, Money, Port


class TestBookingCreation:
    """Tests for Booking creation."""

    def test_create_booking(self) -> None:
        """Test creating a new booking."""
        booking = Booking.create("BL-001234")
        assert booking.id == "BL-001234"
        assert booking.status == BookingStatus.PENDING
        assert booking.client is None
        assert booking.pol is None
        assert booking.pod is None
        assert booking.revenue_charges == []
        assert booking.cost_charges == []

    def test_booking_has_uuid(self) -> None:
        """Test that booking has internal UUID."""
        booking = Booking.create("BL-001234")
        assert booking._uuid is not None


class TestBookingCalculations:
    """Tests for Booking financial calculations."""

    def test_total_revenue_empty(self) -> None:
        """Test total revenue with no charges."""
        booking = Booking.create("BL-001")
        assert booking.total_revenue == Money.zero()

    def test_total_costs_empty(self) -> None:
        """Test total costs with no charges."""
        booking = Booking.create("BL-001")
        assert booking.total_costs == Money.zero()

    def test_total_revenue_with_charges(self) -> None:
        """Test total revenue calculation."""
        booking = Booking.create("BL-001")
        invoice_id = uuid4()

        charge1 = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,  # Revenue
            container=None,
            description="Freight",
            amount=Money.from_float(1000.00),
        )
        charge2 = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.HANDLING,
            provider_type=None,
            container=None,
            description="Handling",
            amount=Money.from_float(500.00),
        )

        booking.add_revenue_charge(charge1)
        booking.add_revenue_charge(charge2)

        assert booking.total_revenue == Money.from_float(1500.00)

    def test_total_costs_with_charges(self) -> None:
        """Test total costs calculation."""
        booking = Booking.create("BL-001")
        invoice_id = uuid4()

        charge1 = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container="CONT001",
            description="Ocean Freight",
            amount=Money.from_float(800.00),
        )
        charge2 = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.TRANSPORT,
            provider_type=ProviderType.CARRIER,
            container="CONT001",
            description="Land Transport",
            amount=Money.from_float(300.00),
        )

        booking.add_cost_charge(charge1)
        booking.add_cost_charge(charge2)

        assert booking.total_costs == Money.from_float(1100.00)

    def test_margin_positive(self) -> None:
        """Test margin calculation with positive result."""
        booking = Booking.create("BL-001")
        invoice_id = uuid4()

        # Revenue: 1500
        revenue = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Revenue",
            amount=Money.from_float(1500.00),
        )
        booking.add_revenue_charge(revenue)

        # Costs: 1000
        cost = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Cost",
            amount=Money.from_float(1000.00),
        )
        booking.add_cost_charge(cost)

        assert booking.margin == Money.from_float(500.00)

    def test_margin_negative(self) -> None:
        """Test margin calculation with negative result (costs > revenue)."""
        booking = Booking.create("BL-001")
        invoice_id = uuid4()

        # Revenue: 500
        revenue = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Revenue",
            amount=Money.from_float(500.00),
        )
        booking.add_revenue_charge(revenue)

        # Costs: 1000
        cost = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Cost",
            amount=Money.from_float(1000.00),
        )
        booking.add_cost_charge(cost)

        assert booking.margin == Money.from_float(-500.00)
        assert booking.margin.is_negative()

    def test_margin_percentage(self) -> None:
        """Test margin percentage calculation."""
        booking = Booking.create("BL-001")
        invoice_id = uuid4()

        # Revenue: 1000
        revenue = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Revenue",
            amount=Money.from_float(1000.00),
        )
        booking.add_revenue_charge(revenue)

        # Costs: 600
        cost = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Cost",
            amount=Money.from_float(600.00),
        )
        booking.add_cost_charge(cost)

        # Margin: 400, Margin %: 40%
        assert booking.margin_percentage == Decimal("40.00")

    def test_margin_percentage_no_revenue(self) -> None:
        """Test margin percentage with no revenue."""
        booking = Booking.create("BL-001")
        assert booking.margin_percentage == Decimal("0.00")

    def test_commission_calculation(self) -> None:
        """Test agent commission calculation."""
        booking = Booking.create("BL-001")
        invoice_id = uuid4()

        # Revenue: 1000, Costs: 600, Margin: 400
        revenue = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Revenue",
            amount=Money.from_float(1000.00),
        )
        booking.add_revenue_charge(revenue)

        cost = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Cost",
            amount=Money.from_float(600.00),
        )
        booking.add_cost_charge(cost)

        # Commission: 400 * 0.50 = 200
        commission = booking.calculate_agent_commission()
        assert commission == Money.from_float(200.00)

    def test_commission_custom_rate(self) -> None:
        """Test commission with custom rate."""
        booking = Booking.create("BL-001")
        invoice_id = uuid4()

        revenue = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Revenue",
            amount=Money.from_float(1000.00),
        )
        booking.add_revenue_charge(revenue)

        cost = BookingCharge(
            booking_id="BL-001",
            invoice_id=invoice_id,
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Cost",
            amount=Money.from_float(600.00),
        )
        booking.add_cost_charge(cost)

        # Commission: 400 * 0.40 = 160
        commission = booking.calculate_agent_commission(Decimal("0.40"))
        assert commission == Money.from_float(160.00)


class TestBookingStatus:
    """Tests for Booking status management."""

    def test_initial_status_pending(self) -> None:
        """Test that new bookings are pending."""
        booking = Booking.create("BL-001")
        assert booking.status == BookingStatus.PENDING
        assert not booking.is_complete

    def test_mark_complete(self) -> None:
        """Test marking booking as complete."""
        booking = Booking.create("BL-001")
        booking.mark_complete()
        assert booking.status == BookingStatus.COMPLETE
        assert booking.is_complete

    def test_revert_to_pending(self) -> None:
        """Test reverting booking to pending."""
        booking = Booking.create("BL-001")
        booking.mark_complete()
        booking.revert_to_pending()
        assert booking.status == BookingStatus.PENDING
        assert not booking.is_complete


class TestBookingChargeValidation:
    """Tests for charge validation."""

    def test_add_charge_wrong_booking_id(self) -> None:
        """Test that adding charge with wrong booking_id raises error."""
        booking = Booking.create("BL-001")
        charge = BookingCharge(
            booking_id="BL-002",  # Wrong ID
            invoice_id=uuid4(),
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Test",
            amount=Money.from_float(100.00),
        )
        with pytest.raises(ValueError, match="does not match"):
            booking.add_revenue_charge(charge)

    def test_add_cost_charge_wrong_booking_id(self) -> None:
        """Test that adding cost charge with wrong booking_id raises error."""
        booking = Booking.create("BL-001")
        charge = BookingCharge(
            booking_id="BL-002",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Test",
            amount=Money.from_float(100.00),
        )
        with pytest.raises(ValueError, match="does not match"):
            booking.add_cost_charge(charge)

    def test_remove_charges_for_invoice_removes_matching_revenue_and_cost(self) -> None:
        """Test removing charges linked to a specific invoice id."""
        booking = Booking.create("BL-001")
        removed_invoice_id = uuid4()
        kept_invoice_id = uuid4()

        booking.add_revenue_charge(
            BookingCharge(
                booking_id="BL-001",
                invoice_id=removed_invoice_id,
                charge_category=ChargeCategory.FREIGHT,
                provider_type=None,
                container=None,
                description="Revenue removed",
                amount=Money.from_float(100.00),
            )
        )
        booking.add_cost_charge(
            BookingCharge(
                booking_id="BL-001",
                invoice_id=removed_invoice_id,
                charge_category=ChargeCategory.TRANSPORT,
                provider_type=ProviderType.CARRIER,
                container=None,
                description="Cost removed",
                amount=Money.from_float(40.00),
            )
        )
        booking.add_revenue_charge(
            BookingCharge(
                booking_id="BL-001",
                invoice_id=kept_invoice_id,
                charge_category=ChargeCategory.HANDLING,
                provider_type=None,
                container=None,
                description="Revenue kept",
                amount=Money.from_float(60.00),
            )
        )

        changed = booking.remove_charges_for_invoice(removed_invoice_id)

        assert changed is True
        assert all(c.invoice_id != removed_invoice_id for c in booking.revenue_charges)
        assert all(c.invoice_id != removed_invoice_id for c in booking.cost_charges)
        assert len(booking.revenue_charges) == 1
        assert booking.revenue_charges[0].invoice_id == kept_invoice_id
        assert len(booking.cost_charges) == 0

    def test_remove_charges_for_invoice_returns_false_when_no_match(self) -> None:
        """Test remove operation is a no-op when invoice id is not present."""
        booking = Booking.create("BL-001")
        booking.add_revenue_charge(
            BookingCharge(
                booking_id="BL-001",
                invoice_id=uuid4(),
                charge_category=ChargeCategory.FREIGHT,
                provider_type=None,
                container=None,
                description="Revenue",
                amount=Money.from_float(100.00),
            )
        )

        changed = booking.remove_charges_for_invoice(uuid4())

        assert changed is False
        assert len(booking.revenue_charges) == 1


class TestBookingProperties:
    """Tests for Booking property checks."""

    def test_has_revenue(self) -> None:
        """Test has_revenue property."""
        booking = Booking.create("BL-001")
        assert not booking.has_revenue

        charge = BookingCharge(
            booking_id="BL-001",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.FREIGHT,
            provider_type=None,
            container=None,
            description="Test",
            amount=Money.from_float(100.00),
        )
        booking.add_revenue_charge(charge)
        assert booking.has_revenue

    def test_has_costs(self) -> None:
        """Test has_costs property."""
        booking = Booking.create("BL-001")
        assert not booking.has_costs

        charge = BookingCharge(
            booking_id="BL-001",
            invoice_id=uuid4(),
            charge_category=ChargeCategory.FREIGHT,
            provider_type=ProviderType.SHIPPING,
            container=None,
            description="Test",
            amount=Money.from_float(100.00),
        )
        booking.add_cost_charge(charge)
        assert booking.has_costs


class TestBookingUpdates:
    """Tests for Booking update methods."""

    def test_update_client(self) -> None:
        """Test updating client info."""
        booking = Booking.create("BL-001")
        client = ClientInfo(client_id=uuid4(), name="Test Client", nif="A12345678")
        booking.update_client(client)
        assert booking.client == client

    def test_update_ports(self) -> None:
        """Test updating port info."""
        booking = Booking.create("BL-001")
        pol = Port(code="ESVAL", name="Valencia")
        pod = Port(code="CNSGH", name="Shanghai")
        booking.update_ports(pol=pol, pod=pod)
        assert booking.pol == pol
        assert booking.pod == pod

    def test_update_bl_reference(self) -> None:
        """Test updating BL reference."""
        booking = Booking.create("BL-001")
        booking.update_bl_reference("BL-001-CORRECTED")
        assert booking.id == "BL-001-CORRECTED"
