from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.database import get_local_db
from app.services.engagement.retention_predictor import predict_retention

router = APIRouter(prefix="/engagement", tags=["Engagement"])

class RetentionInput(BaseModel):
    user_id: int

@router.get("/retention-risk")
def retention_api(user_id: int, db: Session = Depends(get_local_db)):
    return predict_retention(db, user_id)
