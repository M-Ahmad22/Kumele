# app/db/models_rewards.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric, JSON, func
from sqlalchemy.orm import relationship
from app.db.database import Base

class Event(Base):
    __tablename__ = "events"
    __table_args__ = {"extend_existing": True} 
    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, nullable=False)   # user id who created
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

class UserActivity(Base):
    __tablename__ = "user_activities"
    __table_args__ = {"extend_existing": True} 
    activity_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    activity_type = Column(String, nullable=False)  # 'event_created' or 'event_attended'
    event_id = Column(Integer, nullable=True)
    activity_date = Column(DateTime, nullable=False, server_default=func.now())

class RewardCoupon(Base):
    __tablename__ = "reward_coupons"
    __table_args__ = {"extend_existing": True} 
    coupon_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    status_level = Column(String, nullable=False)  # Bronze|Silver|Gold
    discount_value = Column(Numeric(5,2), nullable=False)
    stackable = Column(Boolean, default=False)
    is_redeemed = Column(Boolean, default=False)
    issued_at = Column(DateTime, server_default=func.now())
    redeemed_at = Column(DateTime, nullable=True)
    meta = Column(JSON, nullable=True)

class RewardStatusHistory(Base):
    __tablename__ = "reward_status_history"
    __table_args__ = {"extend_existing": True} 
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    status_level = Column(String, nullable=False)  # Bronze|Silver|Gold
    awarded_count = Column(Integer, default=1)     # number of stacks for Gold / count for Silver
    issued_at = Column(DateTime, server_default=func.now())
    notes = Column(String, nullable=True)
