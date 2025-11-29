import os
import pickle
import numpy as np
from sqlalchemy import text
from sklearn.ensemble import RandomForestRegressor
from app.db.database import local_engine
from app.config import MODEL_DIR

MODEL_PATH = os.path.join(MODEL_DIR, "discount_model.pkl")

def train_discount_model():
    conn = local_engine.connect()
    rows = conn.execute(text("""
        SELECT ds.value_percent,
               ev.capacity,
               COALESCE(AVG(ue.rating), 3.0) AS rating,
               COUNT(ue.user_id) AS attendance,
               ds.expected_uplift
        FROM discount_suggestions ds
        JOIN events ev ON ev.event_id = ds.event_id
        LEFT JOIN user_events ue ON ue.event_id = ev.event_id
        GROUP BY ds.id, ev.capacity
    """)).fetchall()

    conn.close()

    if len(rows) < 20:
        raise Exception("Not enough discount data to train model")

    X = np.array([[r.value_percent, r.capacity, r.rating, r.attendance] for r in rows])
    y = np.array([r.expected_uplift for r in rows])

    model = RandomForestRegressor(n_estimators=150, random_state=42)
    model.fit(X, y)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    print("✔ Discount model trained and saved:", MODEL_PATH)

if __name__ == "__main__":
    train_discount_model()
