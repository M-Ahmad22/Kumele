# app/services/rewards/rewards_job.py
"""
Manual execution of rewards calculation.
Run:
    python -m app.services.rewards.rewards_job
"""

from sqlalchemy import text
from app.db.database import LocalSessionLocal
from app.services.rewards.rewards_service import generate_coupons_for_user
from app.db import crud_rewards


def compute_all_users():
    with LocalSessionLocal() as db:
        rows = db.execute(text("SELECT DISTINCT user_id FROM user_events")).fetchall()
        if not rows:
            print("No user activity found.")
            return

        for r in rows:
            uid = r[0]
            counts = crud_rewards.get_user_activity_counts(db, uid)
            issued = generate_coupons_for_user(db, uid, counts)
            print(f"User {uid}: events={counts}, issued={len(issued)}")


if __name__ == "__main__":
    compute_all_users()
