# """
# CRUD functions for interacting with PostgreSQL database.
# Used by API routes and ML pipeline to fetch data.
# """

# from sqlalchemy.orm import Session
# from . import models
# from typing import Dict, Any
# from datetime import datetime


# # ------------------------
# # USER QUERIES
# # ------------------------

# def get_all_users(db: Session):
#     """Return all users in DB."""
#     return db.query(models.User).all()


# def get_user_by_id(db: Session, user_id: int):
#     """Fetch a single user by ID."""
#     return db.query(models.User).filter(models.User.user_id == user_id).first()


# # ------------------------
# # EVENTS
# # ------------------------

# def get_all_events(db: Session):
#     """Return all events available in DB."""
#     return db.query(models.Event).all()


# def get_event_by_id(db: Session, event_id: int):
#     """Fetch single event by ID."""
#     return db.query(models.Event).filter(models.Event.event_id == event_id).first()


# # ------------------------
# # USER - EVENT INTERACTIONS
# # ------------------------

# def get_user_event_history(db: Session, user_id: int):
#     """Return events attended / rated by user."""
#     return (
#         db.query(models.UserEvent)
#         .filter(models.UserEvent.user_id == user_id)
#         .all()
#     )


# # ------------------------
# # BLOG CONTENT (for moderation later)
# # ------------------------

# def get_blog_by_id(db: Session, blog_id: int):
#     return (
#         db.query(models.Blog)
#         .filter(models.Blog.blog_id == blog_id)
#         .first()
#     )


# def get_all_blogs(db: Session):
#     return db.query(models.Blog).all()


# # ------------------------
# # INSERT / UPDATE HELPERS
# # ------------------------

# def create_user(db: Session, user: models.User):
#     db.add(user)
#     db.commit()
#     db.refresh(user)
#     return user


# def create_event(db: Session, event: models.Event):
#     db.add(event)
#     db.commit()
#     db.refresh(event)
#     return event


# def save_moderation_result(db: Session, moderation):
#     """
#     moderation is instance of models.ModerationJob
#     """
#     db.add(moderation)
#     db.commit()
#     db.refresh(moderation)
#     return moderation


# def create_moderation_job(db: Session, content_id: str, type_: str, subtype: str, data: str):
#     obj = models.ModerationJob(
#         content_id=content_id,
#         type=type_,
#         subtype=subtype,
#         data=data,
#         status="pending",
#         decision=None,
#         labels=None,
#         worker_notes=None
#     )
#     db.add(obj)
#     db.commit()
#     db.refresh(obj)
#     return obj

# def get_job_by_content_id(db: Session, content_id: str):
#     return db.query(models.ModerationJob).filter(models.ModerationJob.content_id == content_id).first()

# def list_pending_jobs(db: Session, limit: int = 100):
#     return db.query(models.ModerationJob).filter(models.ModerationJob.status == "pending").limit(limit).all()

# def mark_job_processing(db: Session, job_id: int):
#     job = db.query(models.ModerationJob).get(job_id)
#     if not job:
#         return None
#     job.status = "processing"
#     job.processed_at = datetime.utcnow()
#     db.commit()
#     db.refresh(job)
#     return job

# def update_job_result(db: Session, job_id: int, decision: str, labels: Dict[str, Any], notes: str = None):
#     job = db.query(models.ModerationJob).get(job_id)
#     if not job:
#         return None
#     job.status = "completed"
#     job.decision = decision
#     job.labels = labels
#     job.worker_notes = notes
#     job.processed_at = datetime.utcnow()
#     db.commit()
#     db.refresh(job)
#     return job


# app/db/crud.py
from sqlalchemy.orm import Session
from app.db import models
from datetime import datetime
from typing import Dict, Any

def create_moderation_job(db: Session, content_id: str, type_: str, subtype: str|None, data: str):
    job = models.ModerationJob(
        content_id=content_id,
        type=type_,
        subtype=subtype,
        data=data,
        status="pending",
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def get_job_by_content_id(db: Session, content_id: str):
    return db.query(models.ModerationJob).filter(models.ModerationJob.content_id == content_id).first()

def list_pending_jobs(db: Session, limit: int = 100):
    return db.query(models.ModerationJob).filter(models.ModerationJob.status == "pending").limit(limit).all()

def mark_job_processing(db: Session, job_id: int):
    job = db.get(models.ModerationJob, job_id)
    if not job:
        return None
    job.status = "processing"
    job.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job

def update_job_result(db: Session, job_id: int, decision: str, labels: Dict[str, Any], notes: str | None = None):
    job = db.get(models.ModerationJob, job_id)
    if not job:
        return None
    job.status = "completed"
    job.decision = decision
    job.labels = labels
    job.worker_notes = notes
    job.processed_at = datetime.utcnow()
    db.commit()
    db.refresh(job)
    return job
