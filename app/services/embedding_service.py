import os
import threading
import numpy as np
from sentence_transformers import SentenceTransformer

# -------------------------
# Paths
# -------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_PATH = os.path.join(BASE_DIR, "models", "sentence_transformers", "all-MiniLM-L6-v2")

# -------------------------
# Thread-safe lazy load
# -------------------------
_embedding_model = None
_model_lock = threading.Lock()

def get_model():
    """
    Lazy-load the SentenceTransformer model in a thread-safe way.
    """
    global _embedding_model
    if _embedding_model is None:
        with _model_lock:
            if _embedding_model is None:
                print(f"🔄 Loading local SentenceTransformer model from {MODEL_PATH} ...")
                _embedding_model = SentenceTransformer(MODEL_PATH)
                print("✅ Model loaded successfully.")
    return _embedding_model

# -------------------------
# Embedding function
# -------------------------
def get_embedding(texts):
    """
    Convert a string or list of strings to embeddings.
    
    Args:
        texts (str or List[str]): Text(s) to encode.
    
    Returns:
        np.ndarray: Embedding vectors.
    """
    model = get_model()
    if isinstance(texts, str):
        texts = [texts]
    embeddings = np.array(model.encode(texts))
    return embeddings

# -------------------------
# Quick test when run directly
# -------------------------
if __name__ == "__main__":
    sample_texts = ["Hello world!", "This is a test sentence."]
    embeddings = get_embedding(sample_texts)
    print(f"✅ Generated embeddings for {len(sample_texts)} texts. Shape: {embeddings.shape}")
