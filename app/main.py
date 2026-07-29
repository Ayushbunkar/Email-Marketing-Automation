"""FastAPI application factory and startup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.telegram.bot import get_bot_application


from app.db import engine, Base
import app.models  # Ensures all models including User are registered


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager."""
    # Startup: Create tables if they do not exist
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        # Start Telegram bot
        app.state.telegram_app = await get_bot_application()
        if app.state.telegram_app:
            await app.state.telegram_app.initialize()
            if settings.TELEGRAM_WEBHOOK_URL:
                # Webhook mode: We don't call start() or start_polling(),
                # we just need it initialized to accept updates.
                pass
            else:
                # Polling mode
                await app.state.telegram_app.start()
                await app.state.telegram_app.updater.start_polling()
            
    except Exception as e:
        print(f"Error during startup: {e}")
        
    yield
    
    # Shutdown
    if getattr(app.state, "telegram_app", None):
        if settings.TELEGRAM_WEBHOOK_URL:
            # We didn't start the updater in webhook mode
            await app.state.telegram_app.shutdown()
        else:
            await app.state.telegram_app.updater.stop()
            await app.state.telegram_app.stop()
            await app.state.telegram_app.shutdown()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Hermes Email Marketing Agent",
        description="Autonomous email marketing agent powered by open-weight Hermes LLMs",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "env": settings.APP_ENV}

    return app


from app.api.endpoints import campaigns, contacts, analytics, inbox, replies, templates, auth, settings as settings_ep, telegram

# Create the app instance
app = create_app()
app.include_router(campaigns.router)
app.include_router(contacts.router)
app.include_router(analytics.router)
app.include_router(inbox.router)
app.include_router(replies.router)
app.include_router(templates.router)
app.include_router(auth.router)
app.include_router(settings_ep.router)
app.include_router(telegram.router)
