import os
import json
import joblib
import numpy as np
import pandas as pd
from sqlalchemy import text

from app.db.database import local_engine
from app.config import MODEL_DIR
from app.services.ads.ad_trainer import train_ctr_model

CTR_MODEL_PATH = os.path.join(MODEL_DIR, "ctr_model.pkl")
CTR_FEATURES_PATH = os.path.join(MODEL_DIR, "ctr_features.json")


def _load_ctr_model():
    if not os.path.exists(CTR_MODEL_PATH):
        trained = train_ctr_model()
        if not trained:
            return None, None

    model = joblib.load(CTR_MODEL_PATH)
    with open(CTR_FEATURES_PATH) as f:
        features = json.load(f)

    return model, features


def age_mid(s):
    if not s:
        return 30
    if "-" in s:
        lo, hi = s.split("-")
        return (int(lo) + int(hi)) / 2
    return int(s) if s.isdigit() else 30


def predict_ad_performance(ad_id: int):
    sql = text("""
        SELECT ad_id, budget, target_hobby, target_location, target_age_range
        FROM ads WHERE ad_id = :ad LIMIT 1
    """)
    df = pd.read_sql(sql, local_engine, params={"ad": ad_id})

    if df.empty:
        return None

    ad = df.iloc[0]

    model, feature_cols = _load_ctr_model()

    feat = {
        "budget_log": np.log((ad["budget"] or 0) + 1),
        "age_mid": age_mid(ad["target_age_range"]),
        "location_clean": ad["target_location"] or "Unknown",
        "hobby_clean": ad["target_hobby"] or "General",
    }

    X = pd.DataFrame([feat])[feature_cols]

    if model is None:
        ctr = 0.04
    else:
        ctr = float(model.predict(X)[0])

    ctr = max(0, min(ctr, 0.20))
    engagement = ctr * 0.7

    suggestions = []
    if (ad["budget"] or 0) < 100: suggestions.append("Increase budget for more reach.")
    if not ad["target_hobby"]: suggestions.append("Add target hobby.")
    if not ad["target_location"]: suggestions.append("Add location target.")

    return {
        "ad_id": ad_id,
        "predicted_ctr": round(ctr, 4),
        "predicted_engagement": round(engagement, 4),
        "confidence": 0.82,
        "suggestions": suggestions,
    }
