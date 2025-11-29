import os
import joblib
from datetime import datetime
from sqlalchemy import text
from app.config import MODEL_DIR
from sklearn.ensemble import RandomForestClassifier

MODEL_PATH = os.path.join(MODEL_DIR, "retention_model.pkl")


def load_retention_model():
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError("Retention model not trained. Run retention_trainer.py first.")
    return joblib.load(MODEL_PATH)


def predict_retention(db, user_id: int):

    model = load_retention_model()

    # -------------------------
    # Get LAST LOGIN
    # -------------------------
    last_login = db.execute(
        text("SELECT last_login FROM users WHERE user_id = :uid"),
        {"uid": user_id}
    ).scalar()

    if last_login is None:
        return {"error": "User not found"}

    days_since_login = (datetime.now() - last_login).days

    # -------------------------
    # Get LAST EVENT ATTENDED
    # -------------------------
    last_event_date = db.execute(text("""
        SELECT MAX(e.end_time)
        FROM user_events ue
        JOIN events e ON ue.event_id = e.event_id
        WHERE ue.user_id = :uid
    """), {"uid": user_id}).scalar()

    if last_event_date is None:
        days_since_event = 999  
    else:
        days_since_event = (datetime.now() - last_event_date).days

    # -------------------------
    # Get messages sent (placeholder)
    # -------------------------
    messages_30 = db.execute(text("""
        SELECT COUNT(*) FROM user_messages
        WHERE sender_id = :uid
        AND created_at >= NOW() - INTERVAL '30 days'
    """), {"uid": user_id}).scalar() if False else 0

    # -------------------------
    # Get reward status
    # -------------------------
    reward_status = db.execute(text("""
        SELECT reward_status
        FROM user_retention_risk
        WHERE user_id = :uid
    """), {"uid": user_id}).scalar()

    if reward_status is None:
        reward_status = "Bronze"

    # Convert reward status → numeric
    reward_map = {"Bronze": 1, "Silver": 2, "Gold": 3}
    reward_numeric = reward_map.get(reward_status, 1)

    # -------------------------
    # Prepare feature vector
    # -------------------------
    X = [[
        days_since_login,
        days_since_event,
        messages_30,
        reward_numeric
    ]]

    churn_prob = model.predict_proba(X)[0][1]
    risk_level = (
        "high" if churn_prob > 0.65 else
        "medium" if churn_prob > 0.35 else
        "low"
    )

    # -------------------------
    # Generate retention suggestion
    # -------------------------
    if risk_level == "high":
        action = {
            "type": "discount",
            "value_percent": 10,
            "message": "We miss you! Enjoy 10% off your next event."
        }
    elif risk_level == "medium":
        action = {
            "type": "recommendation",
            "message": "Join events matching your favourite hobbies this week!"
        }
    else:
        action = {
            "type": "reward",
            "value": "Silver Badge",
            "message": "You're amazing! Keep attending to reach Gold!"
        }

    return {
        "user_id": user_id,
        "churn_probability": round(float(churn_prob), 3),
        "risk_level": risk_level,
        "recommended_action": action,
        "feature_insights": {
            "days_since_login": days_since_login,
            "days_since_event": days_since_event,
            "messages_sent_past_30_days": messages_30,
            "reward_status": reward_status
        }
    }
