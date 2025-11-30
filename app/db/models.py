# app/db/models.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, Boolean, Date, Numeric, TIMESTAMP
from sqlalchemy.orm import relationship
from app.db.database import Base
from datetime import datetime
from sqlalchemy.sql import func

class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)  # matches DB
    full_name = Column(String(100))
    email = Column(String(150), unique=True)
    password_hash = Column(String)
    age = Column(Integer)
    gender = Column(String(20))
    city = Column(String(100))
    country = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime)
    last_login = Column(DateTime)


# class Event(Base):
#     __tablename__ = "events"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String)
#     description = Column(String)
#     tags = Column(JSON)
#     latitude = Column(Float)
#     longitude = Column(Float)
#     host_id = Column(Integer)
#     host_status = Column(String, default="none")
#     host_gold_count = Column(Integer, default=0)

# class Event(Base):
#     __tablename__ = "events"

#     event_id = Column(Integer, primary_key=True, index=True)
#     title = Column(String)
#     description = Column(String)
#     tags = Column(JSON)
#     latitude = Column(Float)
#     longitude = Column(Float)
#     host_id = Column(Integer)
#     host_status = Column(String, default="none")
#     host_gold_count = Column(Integer, default=0)

class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, index=True)
    event_name = Column(String(200))
    category = Column(String(100))
    city = Column(String(100))
    country = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    organiser_id = Column(Integer) 
    
    
class ModerationJob(Base):
    __tablename__ = "moderation_jobs"
    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(String(200), nullable=False, unique=True, index=True)
    type = Column(String(50), nullable=False)      # "text" or "image"
    subtype = Column(String(100), nullable=True)
    data = Column(Text, nullable=False)            # text or image url/base64
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed
    decision = Column(String(50), nullable=True)  # approve, reject, needs_review
    labels = Column(JSON, nullable=True)          # e.g. {"toxicity": 0.02, "spam":0.1}
    worker_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

# --- Review model (attendee ratings per event) ---
class Review(Base):
    __tablename__ = "reviews"

    review_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    host_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    communication_responsiveness = Column(Float)
    respect = Column(Float)
    professionalism = Column(Float)
    atmosphere = Column(Float)
    value_for_money = Column(Float)
    comment = Column(String)
    submitted_at = Column(DateTime, server_default=func.now())

# --- Host system reliability metrics ---
class HostMetrics(Base):
    __tablename__ = "host_metrics"

    host_id = Column(Integer, primary_key=True)
    event_completion_ratio = Column(Float, default=0.0)
    attendance_follow_through = Column(Float, default=0.0)
    repeat_attendee_ratio = Column(Float, default=0.0)

# class EventRSVPLog(Base):
#     __tablename__ = "event_rsvp_logs"

#     id = Column(Integer, primary_key=True)
#     event_id = Column(Integer, nullable=False)
#     user_id = Column(Integer, nullable=False)
#     rsvp_status = Column(Integer, nullable=False)  # True/False stored as 1/0
#     rsvp_time = Column(DateTime, server_default=func.now())

class EventRSVP(Base):
    __tablename__ = "event_rsvp_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    rsvp_status = Column(Boolean, nullable=False)  # True/False
    rsvp_time = Column(DateTime, server_default=func.now())

class EventAttendanceLog(Base):
    __tablename__ = "event_attendance_logs"

    id = Column(Integer, primary_key=True)
    event_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    attended = Column(Integer, nullable=False)  # True/False stored as 1/0
    check_in_method = Column(String(20))        # qr, geo, manual
    check_in_time = Column(DateTime)

class TimeseriesDaily(Base):
    __tablename__ = "timeseries_daily"

    ts = Column(DateTime, primary_key=True)
    total_events = Column(Integer)
    total_rsvps = Column(Integer)
    total_attendance = Column(Integer)

class TimeseriesHourly(Base):
    __tablename__ = "timeseries_hourly"

    ts = Column(DateTime, primary_key=True)
    total_events = Column(Integer)
    total_rsvps = Column(Integer)
    total_attendance = Column(Integer)

class FeedbackAnalysis(Base):
    __tablename__ = "feedback_analysis"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    sentiment = Column(String(20))
    themes = Column(JSON)
    keywords = Column(JSON)
    confidence = Column(Float)
    created_at = Column(DateTime, server_default=func.now())


class UserRetentionRisk(Base):
    __tablename__ = "user_retention_risk"

    user_id = Column(Integer, primary_key=True)
    churn_probability = Column(Float)
    risk_level = Column(String(20))
    last_event_date = Column(Date)
    reward_status = Column(String(20))
    recommended_action = Column(JSON)
    updated_at = Column(DateTime, server_default=func.now())
    
class UserEvents(Base):
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    event_id = Column(Integer, nullable=False)
    rating = Column(Float)
    feedback = Column(String)
    payment_method = Column(String)
    amount_paid = Column(Float)
    

# -----------------------------
# Rewards System Models
# -----------------------------
class RewardCoupon(Base):
    __tablename__ = "reward_coupons"

    coupon_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    status_level = Column(String(20))           # Bronze | Silver | Gold
    discount_value = Column(Numeric(5, 2))      # 0.00 / 4.00 / 8.00
    stackable = Column(Boolean, default=False)
    is_redeemed = Column(Boolean, default=False)
    issued_at = Column(TIMESTAMP, server_default=func.now())
    redeemed_at = Column(TIMESTAMP)
    meta = Column(JSON)                         # reason, source, metadata


class RewardHistory(Base):
    __tablename__ = "reward_history"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    status_level = Column(String(20))           # Bronze | Silver | Gold
    awarded_count = Column(Integer, default=1)
    notes = Column(String)
    issued_at = Column(TIMESTAMP, server_default=func.now())