# app/workers/chatbot_schedule.py
from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule.update({
    "daily-kb-reindex": {
        "task": "chatbot.reindex_document",
        "schedule": 24 * 60 * 60,
        "args": ("kb_system_health", "System Health Check", "System status OK.", "en")
    }
})
