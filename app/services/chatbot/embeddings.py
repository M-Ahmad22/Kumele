# app/services/chatbot/embeddings.py
from sentence_transformers import SentenceTransformer
import os
from app import config

MODEL_NAME = config.EMBEDDING_MODEL

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder

def embed_text(text: str):
    model = get_embedder()
    return model.encode(text).tolist()
