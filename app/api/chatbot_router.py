# app/api/chatbot_router.py
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.services.chatbot.chatbot_engine import rag_answer
from app.services.chatbot.knowledgebase_sync import sync_document
from app.workers.chatbot_tasks import reindex_document

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

class Ask(BaseModel):
    user_id: str
    query: str
    language: str = "en"

class Sync(BaseModel):
    doc_id: str
    title: str
    content: str
    language: str = "en"

class Feedback(BaseModel):
    query_id: int
    feedback: str

@router.post("/ask")
async def ask(req: Ask):
    answer, sources = await rag_answer(req.query, req.language, req.user_id)
    return {"answer": answer, "sources": sources}

@router.post("/sync")
async def sync_kb(req: Sync, background: BackgroundTasks):
    background.add_task(reindex_document.delay, req.doc_id, req.title, req.content, req.language)
    return {"status": "sync_started", "doc_id": req.doc_id}

@router.post("/feedback")
async def feedback(req: Feedback):
    from app.db.database import engine
    import sqlalchemy as sa
    with engine.begin() as conn:
        conn.execute(sa.text("""
            UPDATE chatbot_logs SET feedback = :f WHERE id = :id
        """), {"f": req.feedback, "id": req.query_id})
    return {"status": "saved"}

@router.get("/history")
async def history(user_id: str):
    from app.db.database import engine
    import sqlalchemy as sa
    with engine.connect() as conn:
        rows = conn.execute(sa.text("""
            SELECT * FROM chatbot_logs
            WHERE user_id = :u
            ORDER BY created_at DESC
            LIMIT 50
        """), {"u": user_id}).fetchall()
    return {"history": [dict(r) for r in rows]}
