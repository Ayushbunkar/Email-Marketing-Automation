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
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m alembic upgrade head

# Seed demo data
seed:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe scripts/seed_demo.py

# Start development server
dev:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn app.main:app --reload

# Start Celery worker
worker:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m celery -A app.workers.celery_app worker -l info

# Start Celery beat (scheduled tasks)
beat:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m celery -A app.workers.celery_app beat -l info

# Run tests
test:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m pytest -q

# Run linter and formatter
lint:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m ruff check .
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m ruff format --check .

# Generate demo events (for testing)
demo-events:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe scripts/generate_demo_events.py
