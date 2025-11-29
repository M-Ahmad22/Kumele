from app.workers.celery_app import celery_app

celery_app.conf.beat_schedule.update({
    "daily-attendance-model-retrain": {
        "task": "app.workers.train_tasks.retrain_attendance_model",
        "schedule": 24 * 60 * 60,   # every 24 hours
        "options": {"expires": 300},
    },
})