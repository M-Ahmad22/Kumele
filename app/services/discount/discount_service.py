import os
import numpy as np
import pickle
from sqlalchemy import text
from app.db.database import local_engine
from app.config import MODEL_DIR

MODEL_PATH = os.path.join(MODEL_DIR, "discount_model.pkl")

if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        discount_model = pickle.load(f)
else:
    discount_model = None


def compute_discount(event_id, current_price, audience_segment):
    conn = local_engine.connect()

    row = conn.execute(
        text("""
            SELECT category, city, capacity, organiser_id
            FROM events WHERE event_id = :eid
        """), {"eid": event_id}
    ).fetchone()

    if not row:
        return {"error": "Event not found"}

    user_stats = conn.execute(
        text("""
            SELECT COALESCE(AVG(rating), 3.0) AS avg_rating,
                   COUNT(*) AS past_attendance
            FROM user_events ue
            JOIN events e ON e.event_id = ue.event_id
            WHERE e.organiser_id = :hid
        """), {"hid": row.organiser_id}).fetchone()

    conn.close()

    features = np.array([[current_price,
                          row.capacity,
                          user_stats.avg_rating,
                          user_stats.past_attendance]])

    if discount_model:
        uplift_pred = discount_model.predict(features)[0]
    else:
        uplift_pred = min(0.30, max(0.05, (5.0 - user_stats.avg_rating) * 0.05))

    base_discount = round(uplift_pred * 100)

    return {
        "recommended_discount": {
            "type": "Loyalty" if "Gold" in audience_segment else "Standard",
            "segment": audience_segment,
            "value_percent": base_discount,
            "expected_uplift": round(uplift_pred, 4),
            "expiry_hours": 48
        },
        "alternate_suggestions": [
            {"type": "Flash Sale", "value_percent": base_discount + 2, "uplift": round(uplift_pred * 0.9, 4)},
            {"type": "Group Offer", "value_percent": base_discount + 4, "uplift": round(uplift_pred * 1.1, 4)}
        ],
        "confidence": 0.89
    }
