"""FastAPI application factory and startup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup
    yield
    # Shutdown


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Hermes Email Marketing Agent",
        description="Autonomous email marketing agent powered by open-weight Hermes LLMs",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "env": settings.APP_ENV}

    return app


# Create the app instance
app = create_app()
