# app/api/rewards.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_local_db
from app.services.rewards.rewards_service import compute_user_rewards_and_progress

router = APIRouter(
    prefix="/rewards",
    tags=["Rewards & Gamification"]
)

@router.get("/suggestion")
def get_rewards_suggestion(user_id: int, db: Session = Depends(get_local_db)):
    try:
        result = compute_user_rewards_and_progress(db, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
