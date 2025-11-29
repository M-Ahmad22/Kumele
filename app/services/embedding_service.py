# import os
# import threading
# import numpy as np
# from sentence_transformers import SentenceTransformer

# # -------------------------
# # Paths
# # -------------------------
# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# MODEL_PATH = os.path.join(BASE_DIR, "models", "sentence_transformers", "all-MiniLM-L6-v2")

# # -------------------------
# # Thread-safe lazy load
# # -------------------------
# _embedding_model = None
# _model_lock = threading.Lock()

# def get_model():
#     """
#     Lazy-load the SentenceTransformer model in a thread-safe way.
#     """
#     global _embedding_model
#     if _embedding_model is None:
#         with _model_lock:
#             if _embedding_model is None:
#                 print(f"🔄 Loading local SentenceTransformer model from {MODEL_PATH} ...")
#                 _embedding_model = SentenceTransformer(MODEL_PATH)
#                 print("✅ Model loaded successfully.")
#     return _embedding_model

# # -------------------------
# # Embedding function
# # -------------------------
# def get_embedding(texts):
#     """
#     Convert a string or list of strings to embeddings.
    
#     Args:
#         texts (str or List[str]): Text(s) to encode.
    
#     Returns:
#         np.ndarray: Embedding vectors.
#     """
#     model = get_model()
#     if isinstance(texts, str):
#         texts = [texts]
#     embeddings = np.array(model.encode(texts))
#     return embeddings

# # -------------------------
# # Quick test when run directly
# # -------------------------
# if __name__ == "__main__":
#     sample_texts = ["Hello world!", "This is a test sentence."]
#     embeddings = get_embedding(sample_texts)
#     print(f"✅ Generated embeddings for {len(sample_texts)} texts. Shape: {embeddings.shape}")


# FOR CLOUD DEPLOYMENT

import os
import threading
import numpy as np
from sentence_transformers import SentenceTransformer

# -------------------------
# Paths
# -------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

LOCAL_MODEL_DIR = os.path.join(BASE_DIR, "models", "sentence_transformers", "all-MiniLM-L6-v2")

# HuggingFace model name (used if local folder not found)
HF_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

# -------------------------
# Thread-safe lazy load
# -------------------------
_embedding_model = None
_model_lock = threading.Lock()


def _local_model_exists() -> bool:
    """
    Check if a local model folder exists with required files.
    """
    if not os.path.isdir(LOCAL_MODEL_DIR):
        return False
    
    files = os.listdir(LOCAL_MODEL_DIR)
    required = {"config.json", "sentence_bert_config.json"}
    weights = {"pytorch_model.bin", "model.safetensors"}

    return (required & set(files)) and (weights & set(files))


def get_model():
    """
    Load model lazily:
    - If local model folder exists → use it
    - Else → download from HuggingFace automatically
    """
    global _embedding_model

    if _embedding_model is not None:
        return _embedding_model

    with _model_lock:
        if _embedding_model is not None:
            return _embedding_model

        # 1) Local model present → load local
        if _local_model_exists():
            print(f"🔄 Loading LOCAL SentenceTransformer from: {LOCAL_MODEL_DIR}")
            _embedding_model = SentenceTransformer(LOCAL_MODEL_DIR)
            print("✅ Local model loaded.")
            return _embedding_model

        # 2) No local model → download from HF
        print(f"🌐 Local model not found — downloading from HuggingFace: {HF_MODEL_NAME}")
        _embedding_model = SentenceTransformer(HF_MODEL_NAME)
        print("⬇️ Saving downloaded model to:", LOCAL_MODEL_DIR)

        # Create folder and save
        os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)
        _embedding_model.save(LOCAL_MODEL_DIR)

        print("✅ Downloaded + saved model successfully.")
        return _embedding_model


# -------------------------
# Embedding function
# -------------------------
def get_embedding(texts):
    """
    Convert a string or list of strings to embeddings.
    """
    model = get_model()

    if isinstance(texts, str):
        texts = [texts]

    embeddings = np.array(model.encode(texts))
    return embeddings


# -------------------------
# Quick test
# -------------------------
if __name__ == "__main__":
    sample = ["Hello world!", "Embedding test"]
    vecs = get_embedding(sample)
    print("Shape:", vecs.shape)
