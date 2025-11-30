# # app/api/match.py
# from fastapi import APIRouter, Depends, Query
# from sqlalchemy.orm import Session
# from app.db.database import get_local_db
# from app.services.match_service import match_events_for_user

# router = APIRouter(prefix="/match", tags=["Event Matching"])

# # Core logic decoupled from FastAPI
# def get_match_events_logic(user_id: int, db: Session):
#     results = match_events_for_user(db, user_id)
#     return {"user_id": user_id, "matches": results}

# # FastAPI endpoint
# @router.get("/events")
# def get_match_events(user_id: int = Query(...), db: Session = Depends(get_local_db)):
#     return get_match_events_logic(user_id, db)

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_local_db
from app.services.match_service import match_events_for_user_basic

router = APIRouter(prefix="/match", tags=["Event Matching"])

@router.get("/events")
def get_match_events(
    user_id: int = Query(..., description="User ID for basic event matching"),
    db: Session = Depends(get_local_db)
):
    results = match_events_for_user_basic(db, user_id)
    return {"user_id": user_id, "matches": results}
