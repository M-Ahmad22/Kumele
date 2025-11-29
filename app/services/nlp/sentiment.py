# app/services/nlp/sentiment.py

from datetime import datetime
from typing import Optional, Dict

from sqlalchemy import text
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

from app.db.database import local_engine

# ---------------------------------------------------------
# Load HuggingFace Model (ONE-TIME LOAD)
# ---------------------------------------------------------
_model_name = "distilbert-base-uncased-finetuned-sst-2-english"
_tokenizer = AutoTokenizer.from_pretrained(_model_name)
_model = AutoModelForSequenceClassification.from_pretrained(_model_name)
_sentiment_pipe = pipeline("sentiment-analysis", model=_model, tokenizer=_tokenizer)


# ---------------------------------------------------------
# Insert text into UGC content
# ---------------------------------------------------------
def _upsert_ugc_content(
    text_value: str,
    content_type: str,
    ref_id: Optional[int],
    author_id: Optional[int],
    language: Optional[str]
) -> int:

    conn = local_engine.connect()
    try:
        result = conn.execute(
            text("""
                INSERT INTO ugc_content (content_type, ref_id, author_id, text, language, created_at)
                VALUES (:ctype, :ref_id, :author_id, :text, :lang, :ts)
                RETURNING content_id;
            """),
            {
                "ctype": content_type,
                "ref_id": ref_id,
                "author_id": author_id,
                "text": text_value,
                "lang": language,
                "ts": datetime.utcnow(),
            }
        )
        content_id = result.fetchone()[0]
        conn.commit()
        return content_id

    finally:
        conn.close()


# ---------------------------------------------------------
# MAIN SENTIMENT ANALYSIS FUNCTION
# ---------------------------------------------------------
def analyze_sentiment(
    text_value: str,          # <-- FIXED: no more shadowing `text`
    content_type: str = "text",
    ref_id: Optional[int] = None,
    author_id: Optional[int] = None,
    language: Optional[str] = "en"
) -> Dict:

    # SAFETY CHECK
    if not text_value or not text_value.strip():
        return {"sentiment": "neutral", "confidence": 0.0}

    # Run HF model
    result = _sentiment_pipe(text_value[:512])[0]
    raw_label = result["label"].lower()
    score = float(result["score"])

    # Map label
    if raw_label == "positive":
        sentiment_label = "positive"
    elif raw_label == "negative":
        sentiment_label = "negative"
    else:
        sentiment_label = "neutral"

    # Avoid medium-confidence guess
    if 0.4 < score < 0.6:
        sentiment_label = "neutral"

    # Store the content
    content_id = _upsert_ugc_content(
        text_value=text_value,
        content_type=content_type,
        ref_id=ref_id,
        author_id=author_id,
        language=language
    )

    # Store sentiment
    conn = local_engine.connect()
    try:
        conn.execute(
            text("""
                INSERT INTO nlp_sentiment (content_id, sentiment_label, polarity_score, analysed_at)
                VALUES (:cid, :label, :score, :ts)
            """),
            {
                "cid": content_id,
                "label": sentiment_label,
                "score": score,
                "ts": datetime.utcnow(),
            }
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "content_id": content_id,
        "sentiment": sentiment_label,
        "confidence": round(score, 4),
    }
