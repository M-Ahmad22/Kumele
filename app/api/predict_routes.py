# app/api/predict_routes.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
from app.services.prediction.predictor import predict_attendance
from app.services.prediction.trends_predictor import predict_best_times

router = APIRouter(prefix="/predict", tags=["Prediction"])

# -------------------- Request Models --------------------

class EventInput(BaseModel):
    event_title: str
    hobby: str
    location: str
    datetime: str
    host_past_events: int
    avg_host_rating: float
    expected_rsvp: int = 0


# -------------------- Response Models --------------------

class TrendSlot(BaseModel):
    day: str
    time_range: str
    avg_attendance: float

class TrendResponse(BaseModel):
    hobby: str
    location: str
    recommended_times: List[TrendSlot]


# -------------------- Endpoints --------------------

@router.post("/attendance")
def attendance_api(payload: EventInput):
    return predict_attendance(payload.dict())


@router.get("/trends", response_model=TrendResponse)
def trends_api(hobby: str, location: str):
    results = predict_best_times(hobby, location)

    return TrendResponse(
        hobby=hobby,
        location=location,
        recommended_times=[
            TrendSlot(
                day=r["day"],
                time_range=r["time_range"],
                avg_attendance=r["avg_attendance"]
            ) for r in results
        ]
    )
