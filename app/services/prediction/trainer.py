import pandas as pd
import numpy as np
import joblib
import json
import os

from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

from app.services.prediction.data_loader import load_training_data
from app.config import MODEL_DIR

MODEL_PATH = os.path.join(MODEL_DIR, "attendance_model.pkl")
ENCODER_PATH = os.path.join(MODEL_DIR, "attendance_encoder.pkl")
FEATURES_PATH = os.path.join(MODEL_DIR, "attendance_features.json")


def train_attendance_model():
    df = load_training_data()

    if df.empty:
        raise RuntimeError("Training failed — no training data found.")

    # -------------------------
    # Define features
    # -------------------------
    df["duration_hours"] = (df["end_time"] - df["start_time"]).dt.total_seconds() / 3600
    df["weekday"] = df["start_time"].dt.weekday

    feature_cols = [
        "hobby_category",
        "location",
        "latitude",
        "longitude",
        "duration_hours",
        "weekday",
        "rsvp_count",
        "avg_rating",
    ]

    X = df[feature_cols]
    y = df["attendance"]

    # -------------------------
    # One-hot encode categorical
    # -------------------------
    categorical_cols = ["hobby_category", "location"]
    numeric_cols = [c for c in feature_cols if c not in categorical_cols]

    encoder = OneHotEncoder(handle_unknown="ignore")

    column_transform = ColumnTransformer(
        transformers=[
            ("cat", encoder, categorical_cols),
            ("num", "passthrough", numeric_cols),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=200,
        random_state=42
    )

    pipeline = Pipeline([
        ("transform", column_transform),
        ("model", model),
    ])

    pipeline.fit(X, y)

    # -------------------------
    # Save model + encoder + feature names
    # -------------------------
    os.makedirs(MODEL_DIR, exist_ok=True)

    joblib.dump(pipeline, MODEL_PATH)
    joblib.dump(encoder, ENCODER_PATH)

    with open(FEATURES_PATH, "w") as f:
        json.dump(feature_cols, f)

    print("✅ Attendance model trained and saved.")

    return True

if __name__ == "__main__":
    train_attendance_model()