# app/config.py

import os
from dotenv import load_dotenv
import redis
from qdrant_client import QdrantClient

load_dotenv()

# ------------------------
# DATABASES
# ------------------------

REAL_DB_URL = os.getenv("REAL_DB_URL")
LOCAL_DB_URL = os.getenv("LOCAL_DB_URL")   # Neon PostgreSQL

# ------------------------
# REDIS (Railway)
# ------------------------

REDIS_URL = os.getenv("REDIS_URL")
REDIS_TOKEN = None

# Redis client for app usage
redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True
)

# ------------------------
# QDRANT Cloud
# ------------------------

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

# ------------------------
# LLM PROVIDERS
# ------------------------

GROK_API_KEY = os.getenv("GROK_API_KEY")
# TGI_URL = os.getenv("TGI_URL")
TGI_URL = None 

# ------------------------
# TRANSLATION ENGINE (FREE)
# ------------------------

TRANSLATE_URL = os.getenv("TRANSLATE_URL", "https://translate.argosopentech.com")

# ------------------------
# MODEL DIRECTORIES
# ------------------------

MODEL_DIR = os.getenv(
    "MODEL_DIR",
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models_saved"))
)

TFRS_MODEL_DIR = os.path.join(MODEL_DIR, "tfrs_model")
KMEANS_MODEL_DIR = os.path.join(MODEL_DIR, "kmeans_users")

TFRS_USER_EMBEDDINGS = os.path.join(TFRS_MODEL_DIR, "user_embeddings.npy")
TFRS_EVENT_EMBEDDINGS = os.path.join(TFRS_MODEL_DIR, "event_embeddings.npy")
KMEANS_MODEL_PATH = os.path.join(KMEANS_MODEL_DIR, "model.joblib")

# ------------------------
# APP DEFAULTS
# ------------------------

DEFAULT_TOP_N = int(os.getenv("DEFAULT_TOP_N", 5))

# ------------------------
# MODERATION
# ------------------------

TOXICITY_REJECT_THRESHOLD = float(os.getenv("TOXICITY_REJECT_THRESHOLD", 0.7))
TOXICITY_REVIEW_THRESHOLD = float(os.getenv("TOXICITY_REVIEW_THRESHOLD", 0.3))
NUDITY_REJECT_THRESHOLD = float(os.getenv("NUDITY_REJECT_THRESHOLD", 0.75))
NUDITY_REVIEW_THRESHOLD = float(os.getenv("NUDITY_REVIEW_THRESHOLD", 0.4))

# ------------------------
# EMBEDDING MODEL
# ------------------------

EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
 
