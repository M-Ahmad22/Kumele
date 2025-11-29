# from fastapi import APIRouter
# from pydantic import BaseModel
# from typing import List, Dict
# import random

# router = APIRouter(prefix="/predict", tags=["Prediction"])

# # -----------------------
# # Input Model
# # -----------------------
# class EventInput(BaseModel):
#     event_title: str
#     hobby: str
#     date: str
#     time: str
#     location: str
#     is_paid: bool
#     host_past_events: int
#     avg_host_rating: float


# # -----------------------
# # /predict/attendance
# # -----------------------
# @router.post("/attendance")
# def predict_attendance(event: EventInput):
#     """
#     Predicts expected turnout for an event based on its features.
#     """

#     # Dummy model logic — replace with sklearn/XGBoost predictions
#     base = 20
#     host_boost = event.host_past_events * 3
#     rating_boost = int(event.avg_host_rating * 2)
#     hobby_boost = 10 if event.hobby.lower() in ["photography", "music", "sports"] else 5
#     paid_penalty = -5 if event.is_paid else 0

#     prediction = base + host_boost + rating_boost + hobby_boost + paid_penalty
#     lower_bound = int(prediction * 0.8)
#     upper_bound = int(prediction * 1.2)

#     return {
#         "event_id": random.randint(1000, 9999),
#         "predicted_attendance": prediction,
#         "confidence_interval": [lower_bound, upper_bound],
#         "model": "scikit-learn (dummy)",
#     }


# # -----------------------
# # /predict/trends
# # -----------------------
# @router.get("/trends")
# def predict_trends(hobby: str, location: str):
#     """
#     Suggests optimal days/times for events by hobby + location.
#     Powered by time-series forecasting (Prophet).
#     """

#     recommendations = [
#         {"day": "Saturday", "time_range": "14:00-16:00", "avg_attendance": 48},
#         {"day": "Sunday", "time_range": "10:00-12:00", "avg_attendance": 42},
#         {"day": "Wednesday", "time_range": "18:00-20:00", "avg_attendance": 30},
#     ]

#     return {
#         "hobby": hobby,
#         "location": location,
#         "recommended_times": recommendations,
#         "model": "Prophet (dummy)",
#     }

