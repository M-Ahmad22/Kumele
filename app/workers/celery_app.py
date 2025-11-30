# # app/workers/celery_app.py
# from celery import Celery
# from app import config

# celery_app = Celery(
#     "kumele_moderation",
#     broker=config.REDIS_URL,
#     backend=config.REDIS_URL,
# )

# # -----------------------------------------------------
# # WINDOWS FIX — Force solo worker pool
# # -----------------------------------------------------
# celery_app.conf.update(
#     worker_pool="solo",        # prevents WinError 5
#     worker_concurrency=1       # solo = single worker process
# )

# # -----------------------------------------------------
# # Route existing moderation queue
# # -----------------------------------------------------
# celery_app.conf.task_routes = {
#     "app.workers.tasks.process_moderation_task": {"queue": "moderation_queue"}
# }

# # -----------------------------------------------------
# # IMPORTANT: Register all task modules
# # -----------------------------------------------------
# from app.workers import tasks                     # existing moderation tasks
# from app.workers import train_tasks               # attendance retraining
# from app.workers import pricing_tasks             # NEW pricing & discount retrainers

# # -----------------------------------------------------
# # Celery Beat Schedules
# # -----------------------------------------------------
# celery_app.conf.beat_schedule = {
#     # Existing attendance retraining
#     "daily-attendance-model-retrain": {
#         "task": "app.workers.train_tasks.retrain_attendance_model",
#         "schedule": 24 * 60 * 60,   # every 24 hours
#         "options": {"expires": 300},
#     },

#     # NEW Pricing model auto-retrain
#     "daily-pricing-model-retrain": {
#         "task": "pricing_retrain_task",
#         "schedule": 24 * 60 * 60,
#     },

#     # NEW Discount model auto-retrain
#     "daily-discount-model-retrain": {
#         "task": "discount_retrain_task",
#         "schedule": 24 * 60 * 60,
#     },
# }

# app/workers/celery_app.py
from celery import Celery
from app import config

celery_app = Celery(
    "kumele",
    broker=config.REDIS_URL,
    backend=config.REDIS_URL,
)

# ---------------------------
# Windows Fix (Safe globally)
# ---------------------------
celery_app.conf.update(
    worker_pool="solo",
    worker_concurrency=1
)

# ---------------------------
# Queue Routing
# ---------------------------
celery_app.conf.task_routes = {
    "app.workers.tasks.process_moderation_task": {"queue": "moderation_queue"},
    "app.services.rewards.rewards_daily.compute_daily": {"queue": "rewards_queue"},
    "pricing_retrain_task": {"queue": "pricing_queue"},
    "discount_retrain_task": {"queue": "pricing_queue"},
}

# ---------------------------
# Register ALL Tasks
# ---------------------------
from app.workers import tasks            # moderation tasks
from app.workers import train_tasks      # attendance retraining
from app.workers import pricing_tasks    # pricing & discount
from app.services.rewards import rewards_daily  # <-- NEW: daily reward job

# ---------------------------
# CELERY BEAT SCHEDULE (only one beat)
# ---------------------------
celery_app.conf.beat_schedule = {
    # Attendance model retrain
    "daily-attendance-model-retrain": {
        "task": "app.workers.train_tasks.retrain_attendance_model",
        "schedule": 24 * 60 * 60,
    },

    # Pricing model
    "daily-pricing-model-retrain": {
        "task": "pricing_retrain_task",
        "schedule": 24 * 60 * 60,
    },

    # Discount model
    "daily-discount-model-retrain": {
        "task": "discount_retrain_task",
        "schedule": 24 * 60 * 60,
    },

    # -----------------------------
    # ⭐ NEW DAILY REWARD JOB
    # -----------------------------
    "daily-rewards-engine": {
        "task": "app.services.rewards.rewards_daily.compute_daily",
        "schedule": 24 * 60 * 60,   # runs once per day
    }
}
