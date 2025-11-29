from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.services.nlp.sentiment import analyze_sentiment
from app.services.nlp.keywords import extract_keywords_and_store
from app.services.nlp.trends import fetch_trends

router = APIRouter(prefix="/nlp", tags=["NLP"])


class InputText(BaseModel):
    text: str
    content_type: Optional[str] = "text"
    ref_id: Optional[int] = None
    author_id: Optional[int] = None
    language: Optional[str] = "en"


@router.post("/sentiment")
def api_sentiment(payload: InputText):
   return analyze_sentiment(
    text_value=payload.text,
    content_type=payload.content_type,
    ref_id=payload.ref_id,
    author_id=payload.author_id,
    language=payload.language
)


@router.post("/keywords")
def api_keywords(payload: InputText):
    return extract_keywords_and_store(
        text_value=payload.text,
        content_type=payload.content_type,
        ref_id=payload.ref_id,
        author_id=payload.author_id,
        language=payload.language
    )


@router.get("/trends")
def api_trends(timeframe: str = "7d", location: Optional[str] = None, limit: int = 20):
    return fetch_trends(timeframe, location, limit)
