import os
import numpy as np
import pickle
from datetime import datetime
from sqlalchemy import text
from app.db.database import local_engine
from app.config import MODEL_DIR

MODEL_PATH = os.path.join(MODEL_DIR, "pricing_model.pkl")

# --------------------------
# Load trained model
# --------------------------
if os.path.exists(MODEL_PATH):
    with open(MODEL_PATH, "rb") as f:
        pricing_model = pickle.load(f)
else:
    pricing_model = None


# --------------------------
# Fetch historical event context
# --------------------------
def _get_event_context(event_id):
    conn = local_engine.connect()
    row = conn.execute(
        text("""
            SELECT e.event_id, e.category, e.city, e.capacity,
                u.user_id AS host_id,
                COALESCE(AVG(ue.rating), 3.0) AS host_rating
            FROM events e
            LEFT JOIN users u ON e.organiser_id = u.user_id
            LEFT JOIN user_events ue ON ue.event_id = e.event_id
            WHERE e.event_id = :eid
            GROUP BY e.event_id, u.user_id
        """),
        {"eid": event_id}
    ).fetchone()
    conn.close()
    return row


# --------------------------
# Predict attendance for a given price
# --------------------------
def _predict_attendance(price, features):
    if pricing_model is None:
        return max(10, int(200 - price * 0.01))

    X = np.array([[price, features["host_rating"], features["capacity"]]])
    pred = pricing_model.predict(X)[0]
    return max(1, int(pred))


# --------------------------
# Main API Logic
# --------------------------
def compute_optimal_pricing(event_id, base_price):
    ctx = _get_event_context(event_id)
    if not ctx:
        return {"error": "Event not found"}

    features = {
        "host_rating": float(ctx.host_rating),
        "capacity": int(ctx.capacity)
    }

    price_candidates = [
        base_price * 0.9,
        base_price * 1.0,
        base_price * 1.25
    ]

    tiers = []
    for p in price_candidates:
        attendance = _predict_attendance(p, features)
        revenue = p * attendance
        tiers.append({
            "price": round(p, 2),
            "expected_attendance": attendance,
            "revenue": round(revenue, 2)
        })

    tiers_sorted = sorted(tiers, key=lambda x: x["revenue"], reverse=True)
    best = tiers_sorted[0]

    return {
        "recommended_prices": [
            {"tier": "Economy", "price": round(price_candidates[0], 2),
             "expected_attendance": tiers[0]["expected_attendance"]},
            {"tier": "Standard", "price": round(price_candidates[1], 2),
             "expected_attendance": tiers[1]["expected_attendance"]},
            {"tier": "Premium", "price": round(price_candidates[2], 2),
             "expected_attendance": tiers[2]["expected_attendance"]}
        ],
        "optimal_tier": "Standard" if best["price"] == price_candidates[1] else (
            "Economy" if best["price"] == price_candidates[0] else "Premium"
        ),
        "predicted_revenue": best["revenue"],
        "confidence": 0.85
    }
