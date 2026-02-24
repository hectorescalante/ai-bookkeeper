"""Use case for changing booking completion status."""

from backend.ports.output.repositories import BookingRepository


class MarkBookingCompleteUseCase:
    """Toggle booking status between PENDING and COMPLETE."""

    def __init__(self, booking_repo: BookingRepository) -> None:
        self.booking_repo = booking_repo

    def mark_complete(self, bl_reference: str) -> None:
        """Mark a booking as complete."""
        booking = self.booking_repo.find_by_id(bl_reference)
        if booking is None:
            raise ValueError(f"Booking '{bl_reference}' not found")
        booking.mark_complete()
        self.booking_repo.update(booking)

    def revert_to_pending(self, bl_reference: str) -> None:
        """Revert a completed booking back to pending."""
        booking = self.booking_repo.find_by_id(bl_reference)
        if booking is None:
            raise ValueError(f"Booking '{bl_reference}' not found")
        booking.revert_to_pending()
        self.booking_repo.update(booking)
