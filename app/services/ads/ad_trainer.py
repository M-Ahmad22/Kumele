import os
import json
import joblib
import pandas as pd
import numpy as np

from sqlalchemy import text
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline

from app.db.database import local_engine
from app.config import MODEL_DIR

CTR_MODEL_PATH = os.path.join(MODEL_DIR, "ctr_model.pkl")
CTR_FEATURES_PATH = os.path.join(MODEL_DIR, "ctr_features.json")


def train_ctr_model():
    print("📥 Loading ad performance data from local DB...")

    sql = text("""
        SELECT
            a.ad_id,
            a.budget,
            a.target_hobby,
            a.target_location,
            a.target_age_range,
            COUNT(ai.*) AS impressions,
            SUM(CASE WHEN ai.clicked THEN 1 ELSE 0 END) AS clicks,
            SUM(CASE WHEN ai.converted THEN 1 ELSE 0 END) AS conversions
        FROM ads a
        JOIN ad_interactions ai ON ai.ad_id = a.ad_id
        GROUP BY a.ad_id, a.budget, a.target_hobby, a.target_location, a.target_age_range
        HAVING COUNT(ai.*) > 0;
    """)

    df = pd.read_sql(sql, local_engine)

    if df.empty:
        print("⚠️ No interactions found — cannot train model.")
        return False

    df["ctr"] = df["clicks"] / df["impressions"].clip(lower=1)
    df["engagement"] = df["conversions"] / df["impressions"].clip(lower=1)

    df["budget_log"] = np.log(df["budget"].fillna(0) + 1)

    def age_mid(s):
        if not s:
            return 30
        if "-" in s:
            lo, hi = s.split("-")
            return (int(lo) + int(hi)) / 2
        try:
            return int(s)
        except:
            return 30

    df["age_mid"] = df["target_age_range"].apply(age_mid)
    df["location_clean"] = df["target_location"].fillna("Unknown")
    df["hobby_clean"] = df["target_hobby"].fillna("General")

    feature_cols = ["budget_log", "age_mid", "location_clean", "hobby_clean"]

    preproc = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["location_clean", "hobby_clean"]),
            ("num", "passthrough", ["budget_log", "age_mid"]),
        ]
    )

    model = Pipeline([
        ("preproc", preproc),
        ("model", RandomForestRegressor(n_estimators=200, random_state=42))
    ])

    print(f"🧠 Training CTR Model using {len(df)} rows...")
    model.fit(df[feature_cols], df["ctr"])

    preds = model.predict(df[feature_cols])
    print(f"✅ CTR Model R² Score: {r2_score(df['ctr'], preds):.3f}")

    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, CTR_MODEL_PATH)

    with open(CTR_FEATURES_PATH, "w") as f:
        json.dump(feature_cols, f)

    print("💾 CTR Model Saved:", CTR_MODEL_PATH)
    return True

if __name__ == "__main__":
    train_ctr_model()
