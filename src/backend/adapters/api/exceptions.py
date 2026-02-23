"""Exception handlers for API."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse


class APIError(Exception):
    """Base class for API errors."""

    def __init__(self, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


async def value_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    """Handle ValueError exceptions (domain validation errors)."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc), "error_type": "validation_error"},
    )


async def generic_exception_handler(_request: Request, _exc: Exception) -> JSONResponse:
    """Handle generic exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "error_type": "server_error"},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
