# Hermes Email Marketing Agent - Makefile
# Full stack development setup with frontend, backend, and workers

.PHONY: db seed dev dev-all dev-frontend dev-backend worker beat test lint demo-events

# Run database migrations
db:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m alembic upgrade head

# Seed demo data
seed:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe scripts/seed_demo.py

# Start all services (frontend, backend, workers)
dev-all: dev-frontend dev-backend dev-worker

# Start development server (backend only)
dev-backend:
	C:\Users\Rupesh\AppData\Local\Programs\Python\Python312\python.exe -m uvicorn app.main:app --reload

# Start development server (frontend only)
dev-frontend:
	cd frontend/hermes-frontend && npm run dev

# Start Celery worker
dev-worker:
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

# Start everything (frontend + backend + workers)
dev: dev-all