"""Use case for editing booking fields."""

from collections.abc import Callable

from backend.application.dtos import EditBookingRequest
from backend.domain.value_objects import Port
from backend.ports.output.repositories import BookingRepository


class EditBookingUseCase:
    """Edit mutable booking fields and persist changes."""

    def __init__(self, booking_repo: BookingRepository) -> None:
        self.booking_repo = booking_repo

    def execute(self, request: EditBookingRequest) -> None:
        """Apply requested field updates to a booking."""
        booking = self.booking_repo.find_by_id(request.bl_reference)
        if booking is None:
            raise ValueError(f"Booking '{request.bl_reference}' not found")

        if request.vessel is not None:
            normalized_vessel = request.vessel.strip()
            booking.vessel = normalized_vessel or None

        if request.containers is not None:
            booking.containers = [
                container.strip()
                for container in request.containers
                if container.strip()
            ]

        self._apply_port_update(
            current_code=booking.pol.code if booking.pol else None,
            current_name=booking.pol.name if booking.pol else None,
            requested_code=request.pol_code,
            requested_name=request.pol_name,
            assign_port=lambda port: setattr(booking, "pol", port),
            port_label="POL",
        )
        self._apply_port_update(
            current_code=booking.pod.code if booking.pod else None,
            current_name=booking.pod.name if booking.pod else None,
            requested_code=request.pod_code,
            requested_name=request.pod_name,
            assign_port=lambda port: setattr(booking, "pod", port),
            port_label="POD",
        )

        self.booking_repo.update(booking)

    @staticmethod
    def _apply_port_update(
        *,
        current_code: str | None,
        current_name: str | None,
        requested_code: str | None,
        requested_name: str | None,
        assign_port: Callable[[Port | None], None],
        port_label: str,
    ) -> None:
        if requested_code is None and requested_name is None:
            return

        code_value = current_code if requested_code is None else requested_code.strip()
        name_value = current_name if requested_name is None else requested_name.strip()

        if not code_value:
            if name_value:
                raise ValueError(f"{port_label} code is required when setting {port_label} name")
            assign_port(None)
            return

        assign_port(Port(code=code_value.upper(), name=name_value or code_value.upper()))
