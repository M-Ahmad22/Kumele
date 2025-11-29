# app/tasks/rewards_job.py
"""
Standalone script to compute rewards for all users.
Run manually or schedule daily via cron/Windows Task Scheduler.

Usage:
> python -m app.tasks.rewards_job
"""

from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import LocalSessionLocal  # use local session and local db
from app.db import crud_rewards
from app.services.rewards_service import generate_coupons_for_user
from app.db import models as core_models  # if you have a users table model

def compute_all_users():
    # Use context manager to auto-close session
    with LocalSessionLocal() as db:
        # fetch distinct user ids from user_activities
        rows = db.execute(text("SELECT DISTINCT user_id FROM user_activities")).fetchall()
        user_ids = [r[0] for r in rows]

        if not user_ids:
            print("No users with activities found.")
            return

        for uid in user_ids:
            counts = crud_rewards.get_user_activity_counts(db, uid)
            issued = generate_coupons_for_user(db, uid, counts)
            print(f"user {uid}: counts={counts}, issued={len(issued)} coupons")


if __name__ == "__main__":
    compute_all_users()
