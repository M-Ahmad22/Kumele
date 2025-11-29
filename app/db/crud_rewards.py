# app/db/crud_rewards.py
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta

from app.db import models as core_models  # existing models (if any)
from app.db.models_rewards import Event, UserActivity, RewardCoupon, RewardStatusHistory
from typing import Dict, List, Any

def get_30d_window():
    end = datetime.utcnow()
    start = end - timedelta(days=30)
    return start, end

def get_user_activity_counts(db: Session, user_id: int) -> Dict[str, int]:
    start, end = get_30d_window()
    q = db.query(UserActivity.activity_type, func.count().label("cnt")).filter(
        UserActivity.user_id == user_id,
        UserActivity.activity_date >= start,
        UserActivity.activity_date <= end
    ).group_by(UserActivity.activity_type).all()
    counts = {"events_attended": 0, "events_hosted": 0}
    for typ, cnt in q:
        if typ == "event_attended":
            counts["events_attended"] = int(cnt)
        elif typ == "event_created":
            counts["events_hosted"] = int(cnt)
    counts["total_events"] = counts["events_attended"] + counts["events_hosted"]
    return counts

def get_user_unredeemed_coupons(db: Session, user_id: int) -> List[RewardCoupon]:
    return db.query(RewardCoupon).filter(
        RewardCoupon.user_id == user_id,
        RewardCoupon.is_redeemed == False
    ).all()

def issue_coupon(db: Session, user_id: int, status_level: str, discount_value: float, stackable: bool, meta: Dict[str, Any] = None) -> RewardCoupon:
    coupon = RewardCoupon(
        user_id=user_id,
        status_level=status_level,
        discount_value=discount_value,
        stackable=stackable,
        meta=meta or {}
    )
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def mark_coupon_redeemed(db: Session, coupon_id: int):
    coupon = db.query(RewardCoupon).filter(RewardCoupon.coupon_id == coupon_id).first()
    if not coupon:
        return None
    coupon.is_redeemed = True
    coupon.redeemed_at = func.now()
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

def record_status_history(db: Session, user_id: int, status_level: str, awarded_count: int = 1, notes: str = None):
    hist = RewardStatusHistory(
        user_id=user_id,
        status_level=status_level,
        awarded_count=awarded_count,
        notes=notes
    )
    db.add(hist)
    db.commit()
    db.refresh(hist)
    return hist

def get_status_history(db: Session, user_id: int):
    return db.query(RewardStatusHistory).filter(RewardStatusHistory.user_id == user_id).order_by(RewardStatusHistory.issued_at.desc()).all()
