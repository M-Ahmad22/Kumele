from sqlalchemy.orm import Session
from app.db.models import Review, HostMetrics
from datetime import datetime
import numpy as np

def calculate_host_score(db: Session, host_id: int):
    reviews = db.query(Review).filter(Review.host_id == host_id).all()
    metrics = db.query(HostMetrics).filter(HostMetrics.host_id == host_id).first()

    if not reviews:
        return None

    # --- Attendee Ratings Average (each field weighted) ---
    comm = np.mean([r.communication_responsiveness for r in reviews if r.communication_responsiveness is not None]) or 0
    respect = np.mean([r.respect for r in reviews if r.respect is not None]) or 0
    prof = np.mean([r.professionalism for r in reviews if r.professionalism is not None]) or 0
    atm = np.mean([r.atmosphere for r in reviews if r.atmosphere is not None]) or 0
    val = np.mean([r.value_for_money for r in reviews if r.value_for_money is not None]) or 0

    attendee_score = (comm * 0.2 + respect * 0.2 + prof * 0.2 + atm * 0.05 + val * 0.05) / 0.7

    # --- System Reliability Score ---
    if metrics:
        sys_score = (metrics.event_completion_ratio * 0.15 +
                     metrics.attendance_follow_through * 0.10 +
                     metrics.repeat_attendee_ratio * 0.05) / 0.30
    else:
        sys_score = 0

    # --- Final Weighted Host Score ---
    final_score = (0.7 * attendee_score + 0.3 * sys_score)
    avg_reviews = len(reviews)

    return {
        "overall_score": round(final_score, 2),
        "reviews_count": avg_reviews,
        "attendee_ratings": {
            "communication_responsiveness": round(comm, 2),
            "respect": round(respect, 2),
            "professionalism": round(prof, 2),
            "atmosphere": round(atm, 2),
            "value_for_money": round(val, 2)
        },
        "system_reliability": {
            "event_completion_ratio": round(metrics.event_completion_ratio, 2) if metrics else 0,
            "attendance_follow_through": round(metrics.attendance_follow_through, 2) if metrics else 0,
            "repeat_attendee_ratio": round(metrics.repeat_attendee_ratio, 2) if metrics else 0
        },
        "badges": [
            {"label": "Reliable Organiser", "value": f"{int(metrics.event_completion_ratio*100)}% Event Completion"} if metrics else {},
            {"label": "Strong Attendance", "value": f"{int(metrics.attendance_follow_through*100)}% Show Rate"} if metrics else {},
            {"label": "Returning Attendees", "value": f"{int(metrics.repeat_attendee_ratio*100)}% Repeat Users"} if metrics else {}
        ],
        "last_updated": datetime.utcnow().isoformat()
    }

def submit_review(db: Session, data):
    review = Review(**data)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
