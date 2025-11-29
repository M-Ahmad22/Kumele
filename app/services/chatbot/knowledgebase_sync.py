# app/services/chatbot/knowledgebase_sync.py

import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from app.db.database import engine
from app.services.chatbot.embeddings import embed_text, get_embedder
from app.services.chatbot.qdrant_client import ensure_collection, upsert_vectors

SessionLocal = sessionmaker(bind=engine)

def chunk_text(content: str):
    return [p.strip() for p in content.split("\n") if p.strip()]

def sync_document(doc_id, title, content, language):
    session = SessionLocal()

    # Save/update document
    session.execute(sa.text("""
        INSERT INTO knowledge_documents (id, title, content, language, updated_at)
        VALUES (:id, :t, :c, :l, NOW())
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            language = EXCLUDED.language,
            updated_at = NOW();
    """), {"id": doc_id, "t": title, "c": content, "l": language})
    session.commit()

    # Chunk
    chunks = chunk_text(content)
    embedder = get_embedder()
    vector_size = embedder.get_sentence_embedding_dimension()

    ensure_collection(vector_size)

    ids, vectors, payloads = [], [], []

    for i, chunk in enumerate(chunks):
        cid = f"{doc_id}_chunk_{i}"
        vec = embed_text(chunk)

        ids.append(cid)
        vectors.append(vec)
        payloads.append({
            "doc_id": doc_id,
            "title": title,
            "text": chunk,
            "language": language
        })

        session.execute(sa.text("""
            INSERT INTO knowledge_chunks (chunk_id, doc_id, chunk_text, embedding_model, vector_id)
            VALUES (:cid, :d, :txt, :mdl, :vid)
            ON CONFLICT (chunk_id) DO UPDATE SET
                chunk_text = EXCLUDED.chunk_text;
        """), {
            "cid": cid,
            "d": doc_id,
            "txt": chunk,
            "mdl": embedder.__class__.__name__,
            "vid": cid
        })

    session.commit()
    session.close()

    upsert_vectors(ids, vectors, payloads)
    return len(chunks)
