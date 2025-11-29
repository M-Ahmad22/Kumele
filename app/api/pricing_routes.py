# from fastapi import APIRouter
# from pydantic import BaseModel
# from app.services.pricing.pricing_service import pricing_service

# router = APIRouter(prefix="/pricing", tags=["Pricing"])

# class PricingInput(BaseModel):
#     event_id: int
#     host_id: int
#     category: str
#     location: str
#     capacity: int
#     date: str
#     base_price: float

# @router.post("/optimise")
# def optimise_price(payload: PricingInput):
#     return pricing_service.predict_price_range(payload.dict())

from fastapi import APIRouter, Query
from app.services.pricing.pricing_service import compute_optimal_pricing

router = APIRouter(prefix="/pricing", tags=["Dynamic Pricing"])

@router.get("/optimise")
def optimise_price(event_id: int, base_price: float = 1000):
    return compute_optimal_pricing(event_id, base_price)