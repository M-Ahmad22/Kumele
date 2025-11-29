# app/services/rewards_service.py
from typing import Dict, Any
from decimal import Decimal
from app.db import crud_rewards
from sqlalchemy.orm import Session

# Reward definitions
REWARDS = {
    "gold": {"threshold": 4, "discount": Decimal("8.00"), "stackable": True},
    "silver": {"threshold": 3, "discount": Decimal("4.00"), "stackable": False},
    "bronze": {"threshold": 1, "discount": Decimal("0.00"), "stackable": False},
}

def decompose_to_badges(total_events: int):
    """
    Convert total_events into counts:
    - 1 Gold per 4 events
    - from remainder: 1 Silver per 3 events
    - remainder >=1 => 1 Bronze (max 1)
    """
    gold = total_events // REWARDS["gold"]["threshold"]
    rem = total_events - gold * REWARDS["gold"]["threshold"]
    silver = rem // REWARDS["silver"]["threshold"]
    rem2 = rem - silver * REWARDS["silver"]["threshold"]
    bronze = 1 if rem2 >= REWARDS["bronze"]["threshold"] else 0
    return {"gold": int(gold), "silver": int(silver), "bronze": int(bronze)}

def generate_coupons_for_user(db: Session, user_id: int, counts: Dict[str,int]):
    """
    Issue coupons according to decomposition.
    For Gold: issue `gold` coupons (stackable true)
    For Silver: issue `silver` coupons (non-stackable)
    For Bronze: issue up to 1 bronze coupon (non-stackable, discount 0% — it's a badge)
    This function will avoid duplicating identical coupons issued within same day by checking recent issues.
    """
    total = counts["total_events"]
    badges = decompose_to_badges(total)
    issued = []

    # simple deduplication: we will not issue more coupons for same user & status if already exists today and not redeemed.
    existing = crud_rewards.get_user_unredeemed_coupons(db, user_id)
    # Count existing per status level
    existing_counts = {}
    for c in existing:
        existing_counts[c.status_level.lower()] = existing_counts.get(c.status_level.lower(), 0) + 1

    # GOLD
    for _ in range(badges["gold"]):
        already = existing_counts.get("gold", 0)
        # allow issuing additional golds beyond existing count
        # we issue necessary golds to reach badges["gold"]
        if already > 0:
            existing_counts["gold"] = existing_counts["gold"] - 1
            continue
        cp = crud_rewards.issue_coupon(db, user_id, "Gold", float(REWARDS["gold"]["discount"]), True, meta={"reason":"earned_4_events_30d"})
        issued.append(cp)

    # SILVER
    for _ in range(badges["silver"]):
        already = existing_counts.get("silver", 0)
        if already > 0:
            existing_counts["silver"] = existing_counts["silver"] - 1
            continue
        cp = crud_rewards.issue_coupon(db, user_id, "Silver", float(REWARDS["silver"]["discount"]), False, meta={"reason":"earned_3_events_30d"})
        issued.append(cp)

    # BRONZE (max 1)
    if badges["bronze"] == 1:
        already = existing_counts.get("bronze", 0)
        if already == 0:
            cp = crud_rewards.issue_coupon(db, user_id, "Bronze", float(REWARDS["bronze"]["discount"]), False, meta={"reason":"earned_1_event_30d"})
            issued.append(cp)

    # record history entry if any issued
    if issued:
        crud_rewards.record_status_history(db, user_id, "Issued", awarded_count=len(issued), notes="auto-issued via rewards service")

    return issued

def compute_user_rewards_and_progress(db: Session, user_id: int) -> Dict[str,Any]:
    # returns structured data suitable for API response
    counts = crud_rewards.get_user_activity_counts(db, user_id)
    badges = decompose_to_badges(counts["total_events"])

    # progress to next status:
    # if no gold yet, next target is 4 events for gold; else if partial toward next gold, show events remaining to next gold
    next_target = None
    if badges["gold"] >= 0:
        # compute events toward next gold threshold
        events_toward_next_gold = counts["total_events"] % REWARDS["gold"]["threshold"]
        remaining_to_next_gold = REWARDS["gold"]["threshold"] - events_toward_next_gold
        next_target = {
            "next_status_target": "Gold",
            "events_for_next": int(remaining_to_next_gold),
            "events_attended": counts["events_attended"],
            "events_hosted": counts["events_hosted"],
            "total_events": counts["total_events"]
        }

    coupons = [ {
        "coupon_id": c.coupon_id,
        "status_level": c.status_level,
        "discount_value": str(c.discount_value),
        "stackable": c.stackable,
        "is_redeemed": c.is_redeemed,
        "issued_at": str(c.issued_at),
        "meta": c.meta or {}
    } for c in crud_rewards.get_user_unredeemed_coupons(db, user_id) ]

    history = [ {
        "status_level": h.status_level,
        "awarded_count": h.awarded_count,
        "issued_at": str(h.issued_at),
        "notes": h.notes
    } for h in crud_rewards.get_status_history(db, user_id) ]

    current_status = []
    if badges["gold"]:
        current_status.append({
            "level": "Gold",
            "count": badges["gold"],
            "reward": f"{REWARDS['gold']['discount']}% discount on one in-app purchase",
            "stackable": REWARDS["gold"]["stackable"],
            "criteria": "Created or attended 4 events in the last 30 days"
        })
    if badges["silver"]:
        current_status.append({
            "level": "Silver",
            "count": badges["silver"],
            "reward": f"{REWARDS['silver']['discount']}% discount on one in-app purchase",
            "stackable": REWARDS["silver"]["stackable"],
            "criteria": "Created or attended 3 events in the last 30 days (applies to each silver)"
        })
    if badges["bronze"]:
        current_status.append({
            "level": "Bronze",
            "count": badges["bronze"],
            "reward": f"{REWARDS['bronze']['discount']}% (badge only)",
            "stackable": REWARDS['bronze']["stackable"] if 'bronze' in REWARDS else False,
            "criteria": "Created or attended 1 event in the last 30 days"
        })

    return {
        "user_id": user_id,
        "current_status": current_status,
        "progress": next_target,
        "available_discounts": coupons,
        "history": history
    }
