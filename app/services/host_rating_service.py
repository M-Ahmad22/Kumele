from sqlalchemy.orm import Session
from app.db.models import Review, HostMetrics
from datetime import datetime
import numpy as np
import math

# Helper: safe average ignoring NULL & NaN
def safe_avg(values):
    values = [v for v in values if v is not None and not math.isnan(v)]
    return np.mean(values) if values else 0.0


from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
import numpy as np

def calculate_host_score(db: Session, host_id: int):
    # -------------------------
    # 1) FETCH ATTENDEE REVIEWS
    # -------------------------
    reviews = db.execute(text("""
        SELECT communication_responsiveness, respect, professionalism,
               atmosphere, value_for_money
        FROM reviews
        WHERE host_id = :host
    """), {"host": host_id}).fetchall()

    if not reviews:
        return None

    # Compute average for each category
    comm = np.mean([r[0] for r in reviews if r[0] is not None]) or 0
    respect = np.mean([r[1] for r in reviews if r[1] is not None]) or 0
    prof = np.mean([r[2] for r in reviews if r[2] is not None]) or 0
    atm = np.mean([r[3] for r in reviews if r[3] is not None]) or 0
    val = np.mean([r[4] for r in reviews if r[4] is not None]) or 0

    attendee_score = (comm*0.2 + respect*0.2 + prof*0.2 + atm*0.05 + val*0.05) / 0.7

    # -------------------------
    # 2) SYSTEM METRICS (LIVE)
    # -------------------------

    # Event Completion
    total_events = db.execute(text("""
        SELECT COUNT(*) FROM events WHERE organiser_id = :host
    """), {"host": host_id}).scalar()

    completed_events = db.execute(text("""
        SELECT COUNT(*) FROM events
        WHERE organiser_id = :host AND start_time < NOW()
    """), {"host": host_id}).scalar()

    event_completion_ratio = (
        completed_events / total_events if total_events > 0 else 0
    )

    # Attendance follow-through
    total_rsvp_yes = db.execute(text("""
        SELECT COUNT(*) 
        FROM event_rsvp_logs r
        JOIN events e ON e.event_id = r.event_id
        WHERE e.organiser_id = :host AND r.rsvp_status = TRUE
    """), {"host": host_id}).scalar()

    attended_count = db.execute(text("""
        SELECT COUNT(*)
        FROM event_attendance_logs a
        JOIN events e ON e.event_id = a.event_id
        WHERE e.organiser_id = :host AND a.attended = TRUE
    """), {"host": host_id}).scalar()

    attendance_follow_through = (
        attended_count / total_rsvp_yes if total_rsvp_yes > 0 else 0
    )

    # Repeat attendee ratio
    repeat_attendees = db.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT a.user_id, COUNT(*) AS cnt
            FROM event_attendance_logs a
            JOIN events e ON e.event_id = a.event_id
            WHERE e.organiser_id = :host AND a.attended = TRUE
            GROUP BY a.user_id
            HAVING COUNT(*) >= 2
        ) q;
    """), {"host": host_id}).scalar()

    total_attendees = db.execute(text("""
        SELECT COUNT(DISTINCT a.user_id)
        FROM event_attendance_logs a
        JOIN events e ON e.event_id = a.event_id
        WHERE e.organiser_id = :host AND a.attended = TRUE
    """), {"host": host_id}).scalar()

    repeat_attendee_ratio = (
        repeat_attendees / total_attendees if total_attendees > 0 else 0
    )

    # -------------------------
    # FINAL HOST SCORE
    # -------------------------
    sys_score = (
        event_completion_ratio * 0.15 +
        attendance_follow_through * 0.10 +
        repeat_attendee_ratio * 0.05
    ) / 0.30

    final_score = (0.7 * attendee_score) + (0.3 * sys_score)

    return {
        "overall_score": round(final_score, 2),
        "reviews_count": len(reviews),
        "attendee_ratings": {
            "communication_responsiveness": round(comm, 2),
            "respect": round(respect, 2),
            "professionalism": round(prof, 2),
            "atmosphere": round(atm, 2),
            "value_for_money": round(val, 2)
        },
        "system_reliability": {
            "event_completion_ratio": round(event_completion_ratio, 2),
            "attendance_follow_through": round(attendance_follow_through, 2),
            "repeat_attendee_ratio": round(repeat_attendee_ratio, 2)
        },
        "badges": [
            {"label": "Reliable Organiser", "value": f"{int(event_completion_ratio*100)}% Event Completion"},
            {"label": "Strong Attendance", "value": f"{int(attendance_follow_through*100)}% Show Rate"},
            {"label": "Returning Attendees", "value": f"{int(repeat_attendee_ratio*100)}% Repeat Users"}
        ],
        "last_updated": datetime.utcnow().isoformat()
    }


def submit_review(db: Session, data):
    review = Review(**data)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review
