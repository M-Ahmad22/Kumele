from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_local_db
from app.db.models import FeedbackAnalysis
from app.services.feedback.analyzer import analyze_feedback

router = APIRouter(prefix="/feedback", tags=["Feedback"])

class FeedbackInput(BaseModel):
    user_id: int
    feedback_text: str

@router.post("/analysis")
def analyze_feedback_api(payload: FeedbackInput, db: Session = Depends(get_local_db)):
    result = analyze_feedback(payload.feedback_text)

    entry = FeedbackAnalysis(
        user_id=payload.user_id,
        sentiment=result["sentiment"],
        themes=result["themes"],
        keywords=result["keywords"],
        confidence=result["confidence"]
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return result
