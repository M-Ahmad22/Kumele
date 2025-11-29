# app/services/chatbot/chatbot_engine.py

import httpx
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from app.db.database import engine
from app.services.chatbot.embeddings import embed_text
from app.services.chatbot.qdrant_client import search_vectors
from app import config

SessionLocal = sessionmaker(bind=engine)


async def translate(text: str, source: str, target: str):
    """Translate text using Argos OpenTech public API."""
    if source == target:
        return text

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            r = await client.post(
                f"{config.TRANSLATE_URL}/translate",
                json={"q": text, "source": source, "target": target},
            )
            return r.json().get("translatedText", text)
        except Exception:
            return text


async def call_llm(prompt: str):
    """
    Correct Grok API request (X.ai)
    """
    url = "https://api.x.ai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {config.GROK_API_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "grok-2-latest",
        "messages": [
            {"role": "system", "content": "You are Kumele AI Assistant. Stay factual."},
            {"role": "user", "content": prompt}
        ]
    }

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=body)
        data = r.json()

        # ---------------- DEBUG -----------------
        print("🔎 Grok RAW response:", data)
        # ----------------------------------------

        # ❗ If Grok returned an error → raise it cleanly
        if "error" in data:
            return f"Grok LLM error: {data['error']}"

        # Correct output structure
        return data["choices"][0]["message"]["content"]


async def rag_answer(query: str, language: str, user_id: str):
    """
    RAG pipeline:
       1) translate → English
       2) embed → SentenceTransformer
       3) vector search → Qdrant
       4) ask LLM → Grok
       5) translate back to user language
       6) store logs
    """

    # 1) Translate user question to English
    q_en = await translate(query, language, "en")

    # 2) Embed question
    vec = embed_text(q_en)

    # 3) Search Qdrant
    print("🔍 Searching in Qdrant...")
    results = search_vectors(vec, limit=5)
    print(f"🔍 Qdrant returned {len(results)} matches.")

    # Build RAG context
    context = ""
    sources = []

    for r in results:
        payload = r.payload
        context += f"Source: {payload.get('doc_id')}\n{payload.get('text')}\n\n"
        sources.append(payload.get("doc_id"))

    if context.strip() == "":
        context = "No relevant document context found."

    # 4) Build prompt
    prompt = (
        "You are Kumele AI Assistant.\n"
        "Use ONLY the provided context to answer.\n\n"
        f"{context}\n"
        f"User question: {q_en}\n\nAnswer:"
    )

    # 5) LLM call (GROK ONLY)
    answer_en = await call_llm(prompt)

    # 6) Translate answer back
    answer_local = await translate(answer_en, "en", language)

    # 7) Save logs
    session = SessionLocal()
    session.execute(sa.text("""
        INSERT INTO chatbot_logs (user_id, query, response, language, sources)
        VALUES (:u, :q, :r, :l, :s)
    """), {
        "u": user_id,
        "q": query,
        "r": answer_local,
        "l": language,
        "s": sources  # <--- FIXED
    })

    session.commit()
    session.close()

    return answer_local, sources
