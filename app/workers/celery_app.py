"""Celery application for Hermes."""

from celery import Celery
import os

# Get Redis URL from environment
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "hermes",
    broker=redis_url,
    backend=redis_url,
    include=["app.workers.tasks"]
)

# Load configuration
celery_app.config_from_object("app.workers.config")

if __name__ == "__main__":
    celery_app.start()