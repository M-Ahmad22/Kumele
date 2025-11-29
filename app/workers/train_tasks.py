from celery import shared_task
from app.services.prediction.trainer import train_attendance_model

@shared_task(name="app.workers.train_tasks.retrain_attendance_model")
def retrain_attendance_model():
    """
    Periodic task: Retrains attendance prediction model using REAL_DB data.
    """
    try:
        path = train_attendance_model()
        return {"status": "success", "model_path": path}
    except Exception as e:
        return {"status": "error", "details": str(e)}
