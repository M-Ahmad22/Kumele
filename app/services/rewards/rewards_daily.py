# app/services/rewards/rewards_daily.py
"""
Automatic daily rewards computation (run by Celery Beat)
"""

from celery import shared_task
from sqlalchemy import text
from app.db.database import LocalSessionLocal
from app.services.rewards.rewards_service import generate_coupons_for_user
from app.db import crud_rewards


@shared_task(name="rewards.compute_daily")
def compute_daily_rewards():
    """
    Runs once daily.
    Looks at last 30 days activities and assigns badges/coupons.
    """

    with LocalSessionLocal() as db:
        users = db.execute(text("""
            SELECT DISTINCT user_id
            FROM user_events
        """)).fetchall()

        if not users:
            print("No users found for rewards.")
            return "no_users"

        total_issued = 0

        for row in users:
            uid = row[0]
            counts = crud_rewards.get_user_activity_counts(db, uid)
            issued = generate_coupons_for_user(db, uid, counts)
            total_issued += len(issued)

        print(f"Daily rewards done. Total coupons issued: {total_issued}")
        return {"issued": total_issued}
