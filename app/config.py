"""Configuration settings for Hermes email marketing agent."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Core ---
    APP_ENV: str = Field(default="dev", description="Environment: dev | prod")
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://hermes:hermes@localhost:5432/hermes",
        description="PostgreSQL connection URL with asyncpg driver",
    )
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    SECRET_KEY: str = Field(
        default="change-me",
        description="Secret key for session signing and encryption",
    )
    OPERATOR_PASSWORD: str = Field(
        default="change-me",
        description="Password for the single operator account",
    )
    BASE_URL: str = Field(
        default="http://localhost:8000",
        description="Base URL for building unsubscribe/click links",
    )

    # --- LLM ---
    LLM_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="Base URL for OpenAI-compatible LLM endpoint",
    )
    LLM_API_KEY: str = Field(
        default="",
        description="API key for LLM provider (OpenRouter, Nous API, or vLLM)",
    )
    PLANNER_MODEL: str = Field(
        default="nousresearch/hermes-4-405b",
        description="Model name for planner tasks (campaign planning, copywriting)",
    )
    WORKER_MODEL: str = Field(
        default="nousresearch/hermes-4-70b",
        description="Model name for worker tasks (reply classification, personalization)",
    )
    LLM_MAX_TOOL_ITERATIONS: int = Field(
        default=12,
        description="Maximum tool iterations for agent loop",
    )
    LLM_TIMEOUT_SECONDS: int = Field(
        default=120,
        description="Timeout in seconds for LLM requests",
    )

    # --- Email provider ---
    EMAIL_PROVIDER: str = Field(
        default="mock",
        description="Email provider: mock | resend | brevo",
    )
    RESEND_API_KEY: str = Field(
        default="",
        description="Resend API key (required when EMAIL_PROVIDER=resend)",
    )
    RESEND_WEBHOOK_SECRET: str = Field(
        default="",
        description="Resend webhook secret for signature verification",
    )
    FROM_NAME: str = Field(
        default="Hermes",
        description="Sender name for outgoing emails",
    )
    FROM_EMAIL: str = Field(
        default="hello@mail.example.com",
        description="Sender email address (must be on authenticated sending domain)",
    )
    REPLY_TO_EMAIL: str = Field(
        default="replies@mail.example.com",
        description="Reply-to email address",
    )
    COMPANY_POSTAL_ADDRESS: str = Field(
        default="Acme Pvt Ltd, 1 Example Road, Lucknow, UP 226001, India",
        description="Company postal address for email footer",
    )

    # --- Brevo ---
    BREVO_API_KEY: str = Field(
        default="",
        description="Brevo API key (required when EMAIL_PROVIDER=brevo)",
    )
    BREVO_WEBHOOK_SECRET: str = Field(
        default="",
        description="Brevo webhook secret for signature verification",
    )
    BREVO_INBOUND_WEBHOOK_SECRET: str = Field(
        default="",
        description="Brevo inbound email webhook secret for signature verification",
    )

    # --- Guardrails (hard caps; dispatcher reads these) ---
    MAX_SENDS_PER_DAY: int = Field(
        default=500,
        description="Maximum emails that can be sent in a 24-hour period",
    )
    MAX_SENDS_PER_HOUR: int = Field(
        default=100,
        description="Maximum emails that can be sent in a 1-hour period",
    )
    MAX_EMAILS_PER_CONTACT_PER_WEEK: int = Field(
        default=3,
        description="Maximum emails a single contact can receive in a 7-day period",
    )
    QUIET_HOURS_START: int = Field(
        default=21,
        description="Start hour of quiet hours (24h format, contact-local time)",
    )
    QUIET_HOURS_END: int = Field(
        default=8,
        description="End hour of quiet hours (24h format, contact-local time)",
    )
    AUTO_PAUSE_BOUNCE_RATE: float = Field(
        default=0.02,
        description="Auto-pause threshold: pause all sending above this bounce rate (rolling 24h)",
    )
    AUTO_PAUSE_COMPLAINT_RATE: float = Field(
        default=0.001,
        description="Auto-pause threshold: pause all sending above this complaint rate (rolling 24h)",
    )
    REQUIRE_APPROVAL_FOR_SENDS: bool = Field(
        default=True,
        description="Require human approval before sending emails (never default to false)",
    )


# Single settings object - all modules import from here, never os.environ
settings = Settings()
