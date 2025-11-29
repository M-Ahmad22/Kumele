# app/workers/chatbot_tasks.py
from celery import shared_task
from app.services.chatbot.knowledgebase_sync import sync_document

@shared_task(name="chatbot.reindex_document")
def reindex_document(doc_id, title, content, language):
    chunks = sync_document(doc_id, title, content, language)
    return {"doc_id": doc_id, "chunks": chunks}
