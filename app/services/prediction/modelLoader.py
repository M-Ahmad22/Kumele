# services/prediction/modelLoader.py

import os
import joblib
from app.services.prediction.trainer import train_attendance_model
from app.config import MODEL_DIR

ATTENDANCE_MODEL_PATH = os.path.join(MODEL_DIR, "attendance_model.pkl")

def load_attendance_model():
    if not os.path.exists(ATTENDANCE_MODEL_PATH):
        print("Model missing — training new attendance model...")
        train_attendance_model()

    return joblib.load(ATTENDANCE_MODEL_PATH)
