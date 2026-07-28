# Hermes Email Marketing Agent

Autonomous email marketing agent powered by open-weight Hermes LLMs.

## Features

- **Campaign Management**: Create and manage email campaigns with multiple steps
- **Contact Management**: CRM with lifecycle stages and segmentation
- **Email Provider Integration**: Support for Resend, Brevo, and mock provider
- **Inbound Email**: Brevo inbound webhooks for replies and engagement
- **Guardrails**: Hard caps on sends, quiet hours, auto-pause on high bounce/complaint rates
- **Approval Workflow**: Human approval for campaigns and reply drafts
- **Agent Loop**: LLM-powered campaign planning, copywriting, and optimization

## Project Structure

```
Email Marketing/
├── app/
│   ├── agent/          # Agent loop and tools
│   ├── config.py       # Configuration
│   ├── db.py           # Database connection
│   ├── llm/            # LLM client
│   ├── models/         # SQLAlchemy models
│   ├── providers/      # Email provider drivers
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   ├── web/            # Web dashboard and API
│   ├── workers/        # Celery workers
│   ├── cli.py          # CLI entry point
│   ├── main.py         # FastAPI app
│   └── __init__.py
├── alembic/            # Database migrations
├── scripts/            # Utility scripts
├── tests/              # Test suite
├── docker-compose.yml  # Docker configuration
├── Makefile            # Build targets
├── pyproject.toml      # Python dependencies
└── .env.example        # Environment variables template
```

## Getting Started

### Prerequisites

- Python 3.12+
- Docker and Docker Compose
- PostgreSQL 16 with pgvector extension
- Redis

### Installation

1. Clone the repository
2. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   ```
3. Start Docker services:
   ```bash
   make up
   ```
4. Run database migrations:
   ```bash
   make db
   ```
5. Seed demo data:
   ```bash
   make seed
   ```
6. Start the development server:
   ```bash
   make dev
   ```

## Development

### Running Tests

```bash
make test
```

### Running Linter

```bash
make lint
```

### Running Celery Worker

```bash
make worker
```

### Running Celery Beat

```bash
make beat
```

## Environment Variables

See `.env.example` for all available configuration options.

## License

MIT