# app/services/nlp/keywords.py

import re
import nltk
from datetime import datetime
from typing import Optional, Dict, List

from sqlalchemy import text
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import redis_client      # ← USE REDIS FROM CONFIG
from app.db.database import local_engine

# -------------------------------------------
# LOAD STOPWORDS
# -------------------------------------------
STOPWORDS = set(stopwords.words("english"))

# -------------------------------------------
# INSERT INTO UGC CONTENT TABLE
# -------------------------------------------
def _insert_ugc(text_value, content_type, ref_id, author_id, language) -> int:
    conn = local_engine.connect()
    try:
        result = conn.execute(
            text("""
                INSERT INTO ugc_content (content_type, ref_id, author_id, text, language, created_at)
                VALUES (:ctype, :ref, :auth, :txt, :lang, :ts)
                RETURNING content_id;
            """),
            {
                "ctype": content_type,
                "ref": ref_id,
                "auth": author_id,
                "txt": text_value,
                "lang": language,
                "ts": datetime.utcnow(),
            }
        )
        content_id = result.fetchone()[0]
        conn.commit()
        return content_id
    finally:
        conn.close()


# -------------------------------------------
# KEYWORD EXTRACTION (TF-IDF)
# -------------------------------------------
def _extract_keywords(text_value: str, top_k: int = 10) -> List[str]:

    clean = re.sub(r"[^a-zA-Z0-9\s]", " ", text_value.lower())
    tokens = [t for t in word_tokenize(clean) if t not in STOPWORDS and len(t) > 2]

    if not tokens:
        return []

    vec = TfidfVectorizer()
    tfidf = vec.fit_transform([" ".join(tokens)])
    scores = tfidf.toarray()[0]
    vocab = vec.get_feature_names_out()

    ranked = sorted(zip(vocab, scores), key=lambda x: x[1], reverse=True)

    return [w for w, _ in ranked[:top_k]]


# -------------------------------------------
# MAIN FUNCTION: STORE + KEYWORDS + REDIS
# -------------------------------------------
def extract_keywords_and_store(
    text_value: str,
    content_type: str = "text",
    ref_id: Optional[int] = None,
    author_id: Optional[int] = None,
    language: Optional[str] = "en",
) -> Dict:

    if not text_value or not text_value.strip():
        return {"keywords": []}

    # 1) Insert UGC
    content_id = _insert_ugc(text_value, content_type, ref_id, author_id, language)

    # 2) Extract Keywords
    keywords = _extract_keywords(text_value)

    # 3) Insert into DB + Stream to Redis
    conn = local_engine.connect()
    try:
        for kw in keywords:
            conn.execute(
                text("""
                    INSERT INTO nlp_keywords (content_id, keyword, keyword_type, relevance, confidence, extracted_at)
                    VALUES (:cid, :kw, 'keyword', 1.0, 0.9, :ts)
                """),
                {"cid": content_id, "kw": kw, "ts": datetime.utcnow()}
            )

            # --- FIXED REDIS STREAM CALL ---
            redis_client.xadd(
                name="nlp_events",
                fields={
                    "keyword": kw,
                    "content_id": str(content_id),
                    "type": "keyword",
                },
                maxlen=100000,
                
            )
        conn.commit()
    finally:
        conn.close()

    return {
        "content_id": content_id,
        "keywords": keywords
    }
