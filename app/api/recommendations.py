
# from fastapi import APIRouter, Depends, Query
# from sqlalchemy.orm import Session
# from app.db.database import get_local_db
# from app.services.match_service import match_events_for_user

# router = APIRouter(prefix="/recommendations", tags=["Event Recommendations"])

# @router.get("/events")
# def get_recommended_events(user_id: int = Query(...), db: Session = Depends(get_local_db)):
#     data = match_events_for_user(db, user_id)
#     return {"user_id": user_id, "recommendations": data}


from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.database import get_local_db
from app.services.match_service import match_events_for_user_ml

router = APIRouter(prefix="/recommendations", tags=["Event Recommendations"])

@router.get("/events")
def get_recommended_events(
    user_id: int = Query(..., description="User ID for ML recommendations"),
    db: Session = Depends(get_local_db)
):
    data = match_events_for_user_ml(db, user_id)
    return {"user_id": user_id, "recommendations": data}
