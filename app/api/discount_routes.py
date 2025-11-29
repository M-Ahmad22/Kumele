# from fastapi import APIRouter
# from pydantic import BaseModel
# from app.services.discount.discount_service import discount_service

# router = APIRouter(prefix="/discount", tags=["Discounts"])

# class DiscountInput(BaseModel):
#     event_id: int
#     host_id: int
#     audience_segment: str
#     current_price: float

# @router.post("/suggestion")
# def suggest_discount(payload: DiscountInput):
#     return discount_service.predict_best_discount(payload.dict())

from fastapi import APIRouter
from app.services.discount.discount_service import compute_discount

router = APIRouter(prefix="/discount", tags=["Dynamic Discounts"])

@router.get("/suggestion")
def discount_suggestion(
    event_id: int,
    current_price: float,
    audience_segment: str
):
    return compute_discount(event_id, current_price, audience_segment)
