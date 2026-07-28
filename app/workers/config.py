"""Celery configuration for Hermes."""

import os

# Broker and backend
broker_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
result_backend = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Timezone
timezone = "UTC"
enable_utc = True

# Task settings
task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]

# Worker settings
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000

# Beat schedule (periodic tasks)
beat_schedule = {
    "send-scheduled-messages": {
        "task": "app.workers.tasks.send_scheduled_messages",
        "schedule": 60.0,  # Every 60 seconds
    },
    "cleanup-old-events": {
        "task": "app.workers.tasks.cleanup_old_events",
        "schedule": 86400.0,  # Every 24 hours
    },
}

# Task routes
task_routes = {
    "app.workers.tasks.send_scheduled_messages": {"queue": "send"},
    "app.workers.tasks.cleanup_old_events": {"queue": "cleanup"},
}
