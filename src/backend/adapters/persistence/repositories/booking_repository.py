"""SQLite repository for Booking aggregate."""

from datetime import date

from sqlalchemy.orm import Session

from backend.adapters.persistence.mappers import (
    booking_to_model,
    model_to_booking,
    set_booking_client_from_data,
)
from backend.adapters.persistence.models.booking import BookingModel
from backend.adapters.persistence.models.party import ClientModel
from backend.domain.entities.booking import Booking
from backend.ports.output.repositories import BookingFilters, BookingRepository, BookingSort


class SqlAlchemyBookingRepository(BookingRepository):
    """SQLite implementation of BookingRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, booking: Booking) -> None:
        """Save a new booking or update existing one."""
        # Check if booking already exists
        existing = self.session.query(BookingModel).filter(BookingModel.id == booking.id).first()

        if existing:
            # Update existing
            self.update(booking)
        else:
            # Create new
            model = booking_to_model(booking)
            self.session.add(model)
            self.session.commit()

    def find_by_id(self, bl_reference: str) -> Booking | None:
        """Find booking by BL reference."""
        model = self.session.query(BookingModel).filter(BookingModel.id == bl_reference).first()

        if model is None:
            return None

        booking = model_to_booking(model)

        # Populate ClientInfo if client_id exists
        if model.client_id:
            client = (
                self.session.query(ClientModel).filter(ClientModel.id == model.client_id).first()
            )
            if client:
                set_booking_client_from_data(booking, str(client.id), client.name, client.nif)

        return booking

    def find_or_create(self, bl_reference: str) -> Booking:
        """Find booking by ID, or create if it doesn't exist."""
        booking = self.find_by_id(bl_reference)

        if booking is None:
            # Create new booking
            booking = Booking.create(bl_reference)
            self.save(booking)

        return booking

    def list_all(
        self, filters: BookingFilters | None = None, sort: BookingSort | None = None
    ) -> list[Booking]:
        """List all bookings with optional filtering and sorting."""
        query = self.session.query(BookingModel)

        # Apply filters
        if filters:
            if filters.client_id:
                query = query.filter(BookingModel.client_id == filters.client_id)
            if filters.status:
                query = query.filter(BookingModel.status == filters.status.value)
            if filters.date_from:
                query = query.filter(
                    BookingModel.created_at >= date.fromisoformat(filters.date_from)
                )
            if filters.date_to:
                query = query.filter(BookingModel.created_at <= date.fromisoformat(filters.date_to))

        # Apply sorting
        if sort:
            if sort.field == "created_at":
                order_col = (
                    BookingModel.created_at.desc() if sort.descending else BookingModel.created_at
                )
            elif sort.field == "margin":
                # Sorting by calculated field (margin) requires computing it
                # For now, we'll order by created_at as fallback
                # TODO: Add computed columns or use raw SQL for complex sorts
                order_col = BookingModel.created_at.desc()
            elif sort.field == "commission":
                # Similar to margin
                order_col = BookingModel.created_at.desc()
            else:
                order_col = BookingModel.created_at.desc()

            query = query.order_by(order_col)
        else:
            query = query.order_by(BookingModel.created_at.desc())

        models = query.all()

        # Convert to domain entities and populate client info
        bookings = []
        for model in models:
            booking = model_to_booking(model)

            # Populate ClientInfo if client_id exists
            if model.client_id:
                client = (
                    self.session.query(ClientModel)
                    .filter(ClientModel.id == model.client_id)
                    .first()
                )
                if client:
                    set_booking_client_from_data(booking, str(client.id), client.name, client.nif)

            bookings.append(booking)

        return bookings

    def update(self, booking: Booking) -> None:
        """Update an existing booking."""
        model = self.session.query(BookingModel).filter(BookingModel.id == booking.id).first()

        if model is None:
            raise ValueError(f"Booking {booking.id} not found")

        # Update model fields from entity
        updated_model = booking_to_model(booking)

        model.uuid = updated_model.uuid
        model.created_at = updated_model.created_at
        model.client_id = updated_model.client_id
        model.pol_code = updated_model.pol_code
        model.pol_name = updated_model.pol_name
        model.pod_code = updated_model.pod_code
        model.pod_name = updated_model.pod_name
        model.vessel = updated_model.vessel
        model.containers = updated_model.containers
        model.status = updated_model.status
        model.revenue_charges = updated_model.revenue_charges
        model.cost_charges = updated_model.cost_charges

        self.session.commit()
