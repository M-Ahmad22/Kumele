# app/api/rewards.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.database import get_local_db  # switched to local DB session
from app.services.rewards_service import compute_user_rewards_and_progress, generate_coupons_for_user
from app.db import crud_rewards

router = APIRouter(prefix="/rewards", tags=["rewards"])

@router.get("/suggestion")
def get_rewards_suggestion(user_id: int = Query(..., description="User ID"), db: Session = Depends(get_local_db)):
    # Read precomputed info (we will compute on demand if no coupons exist)
    data = compute_user_rewards_and_progress(db, user_id)
    return data

# Admin endpoint to trigger compute/issue for single user (used by daily job or testing)
@router.post("/admin/compute_for_user")
def compute_and_issue(user_id: int, db: Session = Depends(get_local_db)):
    counts = crud_rewards.get_user_activity_counts(db, user_id)
    issued = generate_coupons_for_user(db, user_id, counts)
    return {"user_id": user_id, "counts": counts, "issued": [{"coupon_id": c.coupon_id, "status": c.status_level} for c in issued]}

# Admin endpoint to redeem a coupon
@router.post("/admin/redeem_coupon")
def redeem_coupon(coupon_id: int, db: Session = Depends(get_local_db)):
    updated = crud_rewards.mark_coupon_redeemed(db, coupon_id)
    if not updated:
        raise HTTPException(status_code=404, detail="coupon not found")
    return {"coupon_id": updated.coupon_id, "is_redeemed": updated.is_redeemed, "redeemed_at": str(updated.redeemed_at)}
