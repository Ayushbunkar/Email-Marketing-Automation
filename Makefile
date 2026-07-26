# Hermes Email Marketing Agent - Makefile

.PHONY: up down db seed dev worker beat test lint demo-events

# Start Docker services (PostgreSQL and Redis)
up:
	docker-compose up -d

# Stop Docker services
down:
	docker-compose down

# Run database migrations
db:
	poetry run alembic upgrade head

# Seed demo data
seed:
	poetry run python scripts/seed_demo.py

# Start development server
dev:
	poetry run uvicorn app.main:app --reload

# Start Celery worker
worker:
	poetry run celery -A app.workers.celery_app worker -l info

# Start Celery beat (scheduled tasks)
beat:
	poetry run celery -A app.workers.celery_app beat -l info

# Run tests
test:
	poetry run pytest -q

# Run linter and formatter
lint:
	poetry run ruff check .
	poetry run ruff format --check .

# Generate demo events (for testing)
demo-events:
	poetry run python scripts/generate_demo_events.py