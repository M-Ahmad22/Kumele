# app/services/chatbot/qdrant_client.py

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app import config

COLLECTION = "kumele_docs"

client = QdrantClient(
    url=config.QDRANT_URL,
    api_key=config.QDRANT_API_KEY
)

def ensure_collection(vector_size: int):
    """Ensure the collection exists in Qdrant Cloud."""
    collections = client.get_collections().collections
    existing = [c.name for c in collections]

    if COLLECTION not in existing:
        print("⚠️ Collection missing → creating now...")
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )
        print("✅ Collection created.")
    else:
        print("ℹ️ Collection already exists.")


def upsert_vectors(ids, vectors, payloads):
    """Insert or update vectors."""
    points = [
        PointStruct(id=str(ids[i]), vector=vectors[i], payload=payloads[i])
        for i in range(len(ids))
    ]

    print(f"➡️ Upserting {len(points)} vectors to Qdrant...")
    client.upsert(
        collection_name=COLLECTION,
        points=points,
        wait=True
    )
    print("✅ Upsert complete.")


def search_vectors(vector, limit=5):
    """Search vectors safely with auto-collection-check."""
    
    # Prevent 404 errors
    ensure_collection(len(vector))

    print("🔍 Searching in Qdrant...")
    results = client.search(
        collection_name=COLLECTION,
        query_vector=vector,
        limit=limit
    )
    print(f"🔍 Search returned {len(results)} results.")
    return results
