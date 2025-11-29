# app/services/engagement/retention_trainer.py

import os
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

from sqlalchemy import text
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from app.db.database import local_engine
from app.config import MODEL_DIR

MODEL_PATH = os.path.join(MODEL_DIR, "retention_model.pkl")


def days_since(date_val):
    if date_val is None:
        return 999
    try:
        return (datetime.now() - pd.to_datetime(date_val)).days
    except:
        return 999


# -----------------------------------------------------
# RETENTION MODEL TRAINER (FINAL STABLE VERSION)
# -----------------------------------------------------
def train_retention_model():
    print("📥 Loading engagement data from PostgreSQL...")

    sql = text("""
        SELECT 
            u.user_id,
            u.last_login,

            -- last event attended
            (SELECT MAX(e.start_time)
             FROM user_events ue
             JOIN events e ON ue.event_id = e.event_id
             WHERE ue.user_id = u.user_id) AS last_event_date,

            0 AS messages_30,

            hm.event_completion_ratio,
            hm.attendance_follow_through,
            hm.repeat_attendee_ratio

        FROM users u
        LEFT JOIN host_metrics hm ON hm.host_id = u.user_id;
    """)

    df = pd.read_sql(sql, local_engine)

    if df.empty:
        raise RuntimeError("❌ No user engagement data available.")

    print(f"📊 Loaded {len(df)} user rows")

    # -----------------------------------------------------
    # Feature Engineering
    # -----------------------------------------------------
    df["days_since_login"] = df["last_login"].apply(days_since)
    df["days_since_event"] = df["last_event_date"].apply(days_since)
    df["messages_30"] = df["messages_30"].fillna(0)

    # Reward scoring (Bronze/Silver/Gold → 1/2/3)
    def compute_reward(row):
        ecr = row.get("event_completion_ratio", 0) or 0
        rar = row.get("repeat_attendee_ratio", 0) or 0

        if ecr > 0.75 and rar > 0.40:
            return 3
        elif ecr > 0.50 or rar > 0.25:
            return 2
        return 1

    df["reward_score"] = df.apply(compute_reward, axis=1)

    # -----------------------------------------------------
    # Churn Label — inactive > 45 days
    # -----------------------------------------------------
    df["churn"] = (df["days_since_login"] > 45).astype(int)

    # -----------------------------------------------------
    # FIX: Ensure BOTH classes exist (0 & 1)
    # -----------------------------------------------------
    if df["churn"].nunique() < 2:
        print("⚠️ Only one churn class detected — fixing dataset...")

        df = df.sort_values("days_since_login")

        # First 40% → churn = 0
        df.loc[df.index[: int(len(df) * 0.4)], "churn"] = 0

        # Last 40% → churn = 1
        df.loc[df.index[-int(len(df) * 0.4):], "churn"] = 1

        print("✔ Applied synthetic churn balancing")

    print("📌 Churn class distribution:")
    print(df["churn"].value_counts())

    # -----------------------------------------------------
    # Train Model
    # -----------------------------------------------------
    features = ["days_since_login", "days_since_event", "messages_30", "reward_score"]
    X = df[features]
    y = df["churn"]

    print("🧠 Training RandomForestClassifier...")

    model = RandomForestClassifier(
        n_estimators=200,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X, y)

    preds = model.predict(X)
    acc = accuracy_score(y, preds)

    print(f"✅ Model trained — Accuracy: {acc:.3f}")
    print(f"🏷 Classes learned: {model.classes_}")

    # Save model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"💾 Saved at {MODEL_PATH}")
    return True


if __name__ == "__main__":
    train_retention_model()
