import joblib
import json
import os
import numpy as np
import pandas as pd

from app.services.prediction.modelLoader import load_attendance_model
from app.config import MODEL_DIR

FEATURES_PATH = os.path.join(MODEL_DIR, "attendance_features.json")


def predict_attendance(payload: dict):
    model = load_attendance_model()

    with open(FEATURES_PATH, "r") as f:
        feature_cols = json.load(f)

    # -----------------------------------
    # Build feature row
    # -----------------------------------
    df = pd.DataFrame([{
        "hobby_category": payload["hobby"],
        "location": payload["location"],
        "latitude": 0,           # You can improve later
        "longitude": 0,
        "duration_hours": 2,     # If not provided
        "weekday": 2,            # Fake weekday for now
        "rsvp_count": payload.get("expected_rsvp", 0),
        "avg_rating": payload.get("avg_host_rating", 4.0)
    }])

    # Ensure missing columns are added
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0

    df = df[feature_cols]

    pred = model.predict(df)[0]
    lower = int(pred * 0.85)
    upper = int(pred * 1.25)

    return {
        "predicted_attendance": int(pred),
        "confidence_interval": [lower, upper],
        "status": "success"
    }
