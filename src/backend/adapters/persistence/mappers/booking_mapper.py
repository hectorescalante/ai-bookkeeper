"""Mapper for Booking entity."""

from backend.adapters.persistence.mappers.invoice_mapper import (
    deserialize_booking_charge,
    serialize_booking_charge,
)
from backend.adapters.persistence.models.booking import BookingModel
from backend.domain.entities.booking import Booking
from backend.domain.enums import BookingStatus
from backend.domain.value_objects import ClientInfo, Port


def booking_to_model(booking: Booking) -> BookingModel:
    """Convert Booking entity to BookingModel ORM."""
    # Serialize charges to JSON
    revenue_charges_json = [serialize_booking_charge(charge) for charge in booking.revenue_charges]
    cost_charges_json = [serialize_booking_charge(charge) for charge in booking.cost_charges]

    # Extract client ID (nullable)
    client_id = booking.client.client_id if booking.client else None

    # Extract port fields (nullable)
    pol_code = booking.pol.code if booking.pol else None
    pol_name = booking.pol.name if booking.pol else None
    pod_code = booking.pod.code if booking.pod else None
    pod_name = booking.pod.name if booking.pod else None

    return BookingModel(
        id=booking.id,
        uuid=booking._uuid,
        created_at=booking.created_at,
        client_id=client_id,
        pol_code=pol_code,
        pol_name=pol_name,
        pod_code=pod_code,
        pod_name=pod_name,
        vessel=booking.vessel,
        containers=list(booking.containers),
        status=booking.status.value,
        revenue_charges=revenue_charges_json,
        cost_charges=cost_charges_json,
    )


def model_to_booking(model: BookingModel) -> Booking:
    """Convert BookingModel ORM to Booking entity."""
    # Deserialize charges from JSON
    revenue_charges = [deserialize_booking_charge(data) for data in model.revenue_charges]
    cost_charges = [deserialize_booking_charge(data) for data in model.cost_charges]

    # Reconstruct ClientInfo if client_id exists
    # Note: Client name and NIF need to be loaded separately or denormalized
    # For now, we'll need to query this separately in the repository
    client = None
    # This will be handled in repository layer by joining with clients table

    # Reconstruct Port value objects
    pol = Port(code=model.pol_code, name=model.pol_name or "") if model.pol_code else None
    pod = Port(code=model.pod_code, name=model.pod_name or "") if model.pod_code else None

    return Booking(
        id=model.id,
        created_at=model.created_at,
        client=client,
        pol=pol,
        pod=pod,
        vessel=model.vessel,
        containers=model.containers,
        status=BookingStatus(model.status),
        revenue_charges=revenue_charges,
        cost_charges=cost_charges,
        _uuid=model.uuid,
    )


def set_booking_client_from_data(booking: Booking, client_id: str, name: str, nif: str) -> None:
    """Set booking client info from client data.

    Helper function used by repository to populate ClientInfo after joining.
    """
    from uuid import UUID

    booking.client = ClientInfo(client_id=UUID(client_id), name=name, nif=nif)
