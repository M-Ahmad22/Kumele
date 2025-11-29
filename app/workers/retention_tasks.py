from app.workers.celery_app import celery_app
from app.services.engagement.retention_trainer import train_retention_model

@celery_app.task(name="train_retention_model")
def run_retention_training():
    train_retention_model()
    return "Retention model retrained"
