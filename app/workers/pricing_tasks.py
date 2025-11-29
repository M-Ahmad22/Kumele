from celery import shared_task
from app.services.pricing.train_pricing_model import train_pricing_model
from app.services.discount.train_discount_model import train_discount_model

@shared_task(name="pricing_retrain_task")
def pricing_retrain_task():
    try:
        train_pricing_model()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}

@shared_task(name="discount_retrain_task")
def discount_retrain_task():
    try:
        train_discount_model()
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "msg": str(e)}
