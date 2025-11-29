from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_local_db
from app.services.host_rating_service import calculate_host_score, submit_review

router = APIRouter(prefix="/host", tags=["Host Ratings"])

@router.get("/{host_id}/rating")
def get_host_rating(host_id: int, db: Session = Depends(get_local_db)):
    result = calculate_host_score(db, host_id)
    if not result:
        raise HTTPException(status_code=404, detail="No reviews found for host")
    return {"host_id": host_id, **result}

@router.post("/event/{event_id}/rating")
def post_event_rating(event_id: int, payload: dict, db: Session = Depends(get_local_db)):
    required = ["user_id", "host_id", "ratings"]
    if not all(k in payload for k in required):
        raise HTTPException(status_code=400, detail="Missing required fields")

    review_data = {
        "user_id": payload["user_id"],
        "host_id": payload["host_id"],
        "event_id": event_id,
        **payload["ratings"],
        "comment": payload.get("comment"),
    }

    review = submit_review(db, review_data)
    score = calculate_host_score(db, payload["host_id"])

    return {
        "status": "success",
        "message": "Rating submitted successfully.",
        "review_id": review.review_id,
        "host_overall_score": score["overall_score"],
        "reviews_count": score["reviews_count"]
    }
