"""AI Bookkeeper - FastAPI Backend Application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.adapters.api.exceptions import register_exception_handlers
from backend.adapters.api.routes import bookings, config, documents, invoices, outlook

app = FastAPI(
    title="AI Bookkeeper",
    description="AI-powered invoice processing for commercial agents",
    version="0.1.0",
)

# Configure CORS for local Tauri app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["tauri://localhost", "http://localhost:1420"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)

# Register API routers
app.include_router(config.router)
app.include_router(documents.router)
app.include_router(bookings.router)
app.include_router(invoices.router)
app.include_router(outlook.router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
