"""Celery app configuration for Hermes."""

import os

from celery import Celery

# Set default Django settings module
os.environ.setdefault("CELERY_CONFIG_MODULE", "app.workers.config")

# Create Celery app
celery_app = Celery("hermes")

# Load configuration from config module
celery_app.config_from_object("app.workers.config")

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.workers"])

if __name__ == "__main__":
    celery_app.start()
