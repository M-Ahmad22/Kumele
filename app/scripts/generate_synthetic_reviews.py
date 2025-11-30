# app/scripts/generate_fast_reviews.py

import random
from datetime import datetime
from sqlalchemy.orm import Session
from app.db.database import LocalSessionLocal as SessionLocal
from app.db.models import Event, Review, EventAttendanceLog

POSITIVE = [
    "Amazing host! Very organised and friendly.",
    "Loved the experience!",
    "Smooth event and great energy.",
    "Fantastic organisation.",
    "Really enjoyed the vibe!"
]

NEUTRAL = [
    "Event was okay.",
    "Decent and moderate experience.",
    "Average organisation."
]

NEGATIVE = [
    "The event needs better organisation.",
    "Host was not responsive.",
    "Experience could be improved."
]

MIXED = [
    "Good experience but minor issues.",
    "Friendly host but average event.",
    "Good effort but needs polish."
]

COMMENT_MAP = {
    "positive": POSITIVE,
    "neutral": NEUTRAL,
    "negative": NEGATIVE,
    "mixed": MIXED,
}

def generate_ratings(sentiment):
    if sentiment == "positive":
        base = random.uniform(4.4, 5.0)
    elif sentiment == "neutral":
        base = random.uniform(3.0, 4.0)
    elif sentiment == "negative":
        base = random.uniform(1.5, 3.0)
    else:
        base = random.uniform(3.2, 4.4)

    return {
        "communication_responsiveness": round(base + random.uniform(-0.4, 0.2), 1),
        "respect": round(base + random.uniform(-0.2, 0.3), 1),
        "professionalism": round(base + random.uniform(-0.5, 0.2), 1),
        "atmosphere": round(base + random.uniform(-0.7, 0.4), 1),
        "value_for_money": round(base + random.uniform(-0.5, 0.4), 1),
    }

MAX_REVIEWS = 500

def generate_fast_reviews():
    db: Session = SessionLocal()

    print("🔄 Loading limited attendance logs...")

    logs = (
        db.query(EventAttendanceLog)
        .filter(EventAttendanceLog.attended == True)
        .limit(MAX_REVIEWS)
        .all()
    )

    print(f"📌 Using {len(logs)} attendance logs (LIMITED).")

    events = db.query(Event).all()
    host_map = {e.event_id: e.organiser_id for e in events}

    reviews_to_insert = []

    for log in logs:
        user_id = log.user_id
        event_id = log.event_id
        host_id = host_map.get(event_id)

        if not host_id:
            continue

        # Skip existing review
        exists = db.query(Review).filter(
            Review.user_id == user_id,
            Review.event_id == event_id
        ).first()

        if exists:
            continue

        sentiment = random.choice(
            ["positive", "positive", "neutral", "mixed", "negative"]
        )

        ratings = generate_ratings(sentiment)
        comment = random.choice(COMMENT_MAP[sentiment])

        review = Review(
            user_id=user_id,
            host_id=host_id,
            event_id=event_id,
            **ratings,
            comment=comment,
            submitted_at=datetime.utcnow()
        )

        reviews_to_insert.append(review)

    print(f"🚀 Inserting {len(reviews_to_insert)} reviews...")
    db.bulk_save_objects(reviews_to_insert)
    db.commit()
    db.close()

    print("🎉 FAST synthetic reviews generated successfully!")


if __name__ == "__main__":
    print("\n⭐ GENERATING FAST SYNTHETIC REVIEWS ⭐\n")
    generate_fast_reviews()
