# import os

# # -------------------------
# # Environment flags (must be set BEFORE importing transformers/tensorflow)
# # -------------------------
# os.environ["TORCHDYNAMO_DISABLE"] = "1"       # avoid torch-dynamo issues on Windows
# os.environ["TOKENIZERS_PARALLELISM"] = "false"
# os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
# os.environ["TRANSFORMERS_NO_TF"] = "1"        # prevent TF import
# os.environ["TRANSFORMERS_NO_FLAX"] = "1"      # prevent Flax import

# # -------------------------
# # Standard imports
# # -------------------------
# from .celery_app import celery_app
# from sqlalchemy.orm import Session
# import threading
# import io
# import base64
# import requests
# from PIL import Image
# from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline, Pipeline
# from typing import Optional, Dict
# import traceback
# import logging

# # app imports
# from app.db import crud
# from app.db.database import Base, LocalSessionLocal, local_engine
# from app import config

# # -------------------------
# # Logging
# # -------------------------
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("kumele.moderation.worker")

# # -------------------------
# # Ensure DB tables exist (local DB used by worker)
# # -------------------------
# Base.metadata.create_all(bind=local_engine)
# logger.info(f"Worker DB ready. Using: {local_engine.url}")

# # -------------------------
# # Local model paths
# # -------------------------
# BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# MODELS_DIR = os.path.join(BASE_DIR, "models")
# LOCAL_TEXT_MODEL = os.path.join(MODELS_DIR, "text")
# LOCAL_IMAGE_MODEL = os.path.join(MODELS_DIR, "image")

# # -------------------------
# # Globals + lock for lazy load
# # -------------------------
# _text_pipeline: Optional[Pipeline] = None
# _image_pipeline: Optional[Pipeline] = None
# _pipeline_lock = threading.Lock()


# # -------------------------
# # Helper to assert local model existence
# # -------------------------
# def _check_model_folder(folder: str) -> None:
#     if not os.path.isdir(folder):
#         raise FileNotFoundError(f"Local model folder not found: {folder}")

#     present_files = set(os.listdir(folder))
#     weight_candidates = {"pytorch_model.bin", "model.safetensors", "tf_model.h5", "flax_model.msgpack"}
#     if not (present_files & weight_candidates):
#         raise FileNotFoundError(
#             f"No model weights found in {folder}. Expect one of: {', '.join(weight_candidates)}."
#         )

#     if "config.json" not in present_files:
#         raise FileNotFoundError(f"Missing config.json in {folder}.")


# # -------------------------
# # Load text pipeline properly
# # -------------------------
# def _load_text_pipeline() -> Pipeline:
#     global _text_pipeline
#     if _text_pipeline is not None:
#         return _text_pipeline

#     with _pipeline_lock:
#         if _text_pipeline is not None:
#             return _text_pipeline

#         try:
#             _check_model_folder(LOCAL_TEXT_MODEL)
#             logger.info(f"Loading local text model from {LOCAL_TEXT_MODEL}")

#             model = AutoModelForSequenceClassification.from_pretrained(
#                 LOCAL_TEXT_MODEL,
#                 local_files_only=True
#             )
#             tokenizer = AutoTokenizer.from_pretrained(
#                 LOCAL_TEXT_MODEL,
#                 local_files_only=True
#             )

#             _text_pipeline = pipeline(
#                 "text-classification",
#                 model=model,
#                 tokenizer=tokenizer,
#                 top_k=None,  # ✅ replaces deprecated return_all_scores=True
#                 device=-1    # ✅ ensures CPU
#             )

#             logger.info("✅ Local text pipeline loaded successfully.")
#             return _text_pipeline

#         except Exception as e:
#             err = f"❌ Failed to load local text model: {e}"
#             logger.exception(err)
#             raise RuntimeError(err) from e


# # -------------------------
# # (Optional) image model load
# # -------------------------
# def _load_image_pipeline() -> Pipeline:
#     global _image_pipeline
#     if _image_pipeline is not None:
#         return _image_pipeline

#     with _pipeline_lock:
#         if _image_pipeline is not None:
#             return _image_pipeline

#         try:
#             _check_model_folder(LOCAL_IMAGE_MODEL)
#             logger.info(f"Loading local image model from {LOCAL_IMAGE_MODEL}")

#             _image_pipeline = pipeline(
#                 task="image-classification",
#                 model=LOCAL_IMAGE_MODEL,
#                 framework="pt",
#                 device=-1,
#                 local_files_only=True
#             )
#             logger.info("✅ Local image pipeline loaded successfully.")
#             return _image_pipeline

#         except Exception as e:
#             err = f"❌ Failed to load local image model: {e}"
#             logger.exception(err)
#             raise RuntimeError(err) from e


# # -------------------------
# # Decision logic
# # -------------------------
# def decision_from_scores(labels: Dict[str, float]):
#     return "classification_only", labels


# # -------------------------
# # Celery task
# # -------------------------
# @celery_app.task(name="app.workers.tasks.process_moderation_task")
# def process_moderation_task(job_id: int):
#     db: Session = LocalSessionLocal()
#     job = None
#     try:
#         job = crud.mark_job_processing(db, job_id)
#         if not job:
#             return {"error": "job not found", "job_id": job_id}

#         logger.info(f"Processing job {job.id} (type={job.type})")

#         if job.type == "text":
#             try:
#                 pipe = _load_text_pipeline()
#             except Exception as e:
#                 crud.update_job_result(db, job.id, "needs_review", {"error": str(e)}, notes="Model load failed")
#                 return {"job_id": job.id, "error": str(e)}

#             try:
#                 text = (job.data or "")[:10000]
#                 res = pipe(text)

#                 labels = {item["label"].lower(): float(item["score"]) for item in res[0]}
#                 decision, mapped = decision_from_scores(labels)

#             except Exception as e:
#                 tb = traceback.format_exc()
#                 crud.update_job_result(db, job.id, "needs_review", {"error": str(e), "trace": tb}, notes="Pipeline error")
#                 return {"job_id": job.id, "error": str(e)}

#         else:
#             crud.update_job_result(db, job.id, "needs_review", {"error": "unknown type"}, notes="Unknown job type")
#             return {"job_id": job.id, "error": "unknown type"}

#         crud.update_job_result(db, job.id, decision, mapped, notes="Processed locally")
#         return {"job_id": job.id, "decision": decision, "labels": mapped}

#     except Exception as e:
#         tb = traceback.format_exc()
#         safe_id = job.id if job else job_id
#         crud.update_job_result(db, safe_id, "needs_review", {"error": str(e), "trace": tb}, notes="Unexpected error")
#         return {"job_id": safe_id, "error": str(e)}

#     finally:
#         db.close()


# def enqueue_moderation_task(job_id: int):
#     process_moderation_task.apply_async(args=(job_id,), queue="moderation_queue")

# CLOUD DEPLOYMENT FILE CHANGED

import os

# -------------------------
# Environment flags (must be set BEFORE importing transformers/tensorflow)
# -------------------------
os.environ["TORCHDYNAMO_DISABLE"] = "1"       # avoid torch-dynamo issues on Windows
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
os.environ["TRANSFORMERS_NO_TF"] = "1"        # prevent TF import
os.environ["TRANSFORMERS_NO_FLAX"] = "1"      # prevent Flax import

# -------------------------
# Standard imports
# -------------------------
from .celery_app import celery_app
from sqlalchemy.orm import Session
import threading
import io
import base64
import requests
from PIL import Image
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
    Pipeline,
)
from typing import Optional, Dict
import traceback
import logging

# app imports
from app.db import crud
from app.db.database import Base, LocalSessionLocal, local_engine
from app import config

# -------------------------
# Logging
# -------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kumele.moderation.worker")

# -------------------------
# Ensure DB tables exist (local DB used by worker)
# -------------------------
Base.metadata.create_all(bind=local_engine)
logger.info(f"Worker DB ready. Using: {local_engine.url}")

# -------------------------
# Local model paths
# -------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(BASE_DIR, "models")
LOCAL_TEXT_MODEL = os.path.join(MODELS_DIR, "text")
LOCAL_IMAGE_MODEL = os.path.join(MODELS_DIR, "image")

# -------------------------
# Hugging Face model IDs (for fallback download)
# -------------------------
TEXT_MODEL_ID = os.getenv(
    "MODERATION_TEXT_MODEL_ID",
    "your-org/your-text-moderation-model",  # TODO: set in .env
)
IMAGE_MODEL_ID = os.getenv(
    "MODERATION_IMAGE_MODEL_ID",
    "your-org/your-image-moderation-model",  # TODO: set in .env
)

# -------------------------
# Globals + lock for lazy load
# -------------------------
_text_pipeline: Optional[Pipeline] = None
_image_pipeline: Optional[Pipeline] = None
_pipeline_lock = threading.Lock()


# -------------------------
# Helper to assert local model existence
# -------------------------
def _check_model_folder(folder: str) -> None:
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Local model folder not found: {folder}")

    present_files = set(os.listdir(folder))
    weight_candidates = {
        "pytorch_model.bin",
        "model.safetensors",
        "tf_model.h5",
        "flax_model.msgpack",
    }
    if not (present_files & weight_candidates):
        raise FileNotFoundError(
            f"No model weights found in {folder}. "
            f"Expect one of: {', '.join(weight_candidates)}."
        )

    if "config.json" not in present_files:
        raise FileNotFoundError(f"Missing config.json in {folder}.")


# -------------------------
# Text pipeline: local first, then download + cache
# -------------------------
def _load_text_pipeline() -> Pipeline:
    global _text_pipeline
    if _text_pipeline is not None:
        return _text_pipeline

    with _pipeline_lock:
        if _text_pipeline is not None:
            return _text_pipeline

        # 1) Try LOCAL first
        try:
            _check_model_folder(LOCAL_TEXT_MODEL)
            logger.info(f"Loading LOCAL text model from {LOCAL_TEXT_MODEL}")

            model = AutoModelForSequenceClassification.from_pretrained(
                LOCAL_TEXT_MODEL,
                local_files_only=True,
            )
            tokenizer = AutoTokenizer.from_pretrained(
                LOCAL_TEXT_MODEL,
                local_files_only=True,
            )

            _text_pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                top_k=None,  # replaces deprecated return_all_scores=True
                device=-1,   # CPU
            )

            logger.info("✅ Local text pipeline loaded successfully.")
            return _text_pipeline

        except Exception as e:
            logger.warning(
                f"⚠️ Local text model not available or invalid ({e}). "
                f"Falling back to Hugging Face model: {TEXT_MODEL_ID}"
            )

        # 2) Fallback: download from HF Hub, then cache to LOCAL_TEXT_MODEL
        try:
            if not TEXT_MODEL_ID or "your-org/your-text-moderation-model" in TEXT_MODEL_ID:
                raise RuntimeError(
                    "MODERATION_TEXT_MODEL_ID is not set. Please set it in your .env "
                    "to a valid Hugging Face model id."
                )

            logger.info(f"⬇️ Downloading text model from Hugging Face: {TEXT_MODEL_ID}")
            model = AutoModelForSequenceClassification.from_pretrained(TEXT_MODEL_ID)
            tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_ID)

            # Cache locally for next run
            os.makedirs(LOCAL_TEXT_MODEL, exist_ok=True)
            model.save_pretrained(LOCAL_TEXT_MODEL)
            tokenizer.save_pretrained(LOCAL_TEXT_MODEL)
            logger.info(f"💾 Text model cached at {LOCAL_TEXT_MODEL}")

            _text_pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                top_k=None,
                device=-1,
            )
            logger.info("✅ Remote text pipeline loaded successfully.")
            return _text_pipeline

        except Exception as e:
            err = f"❌ Failed to load text model (local and remote): {e}"
            logger.exception(err)
            raise RuntimeError(err) from e


# -------------------------
# Image pipeline: local first, then download + cache
# -------------------------
def _load_image_pipeline() -> Pipeline:
    """
    Optional image moderation pipeline.
    Same pattern: try local folder, else download from HF and cache.
    """
    global _image_pipeline
    if _image_pipeline is not None:
        return _image_pipeline

    with _pipeline_lock:
        if _image_pipeline is not None:
            return _image_pipeline

        # 1) Try LOCAL first
        try:
            _check_model_folder(LOCAL_IMAGE_MODEL)
            logger.info(f"Loading LOCAL image model from {LOCAL_IMAGE_MODEL}")

            _image_pipeline = pipeline(
                task="image-classification",
                model=LOCAL_IMAGE_MODEL,
                framework="pt",
                device=-1,
                local_files_only=True,
            )
            logger.info("✅ Local image pipeline loaded successfully.")
            return _image_pipeline

        except Exception as e:
            logger.warning(
                f"⚠️ Local image model not available or invalid ({e}). "
                f"Falling back to Hugging Face model: {IMAGE_MODEL_ID}"
            )

        # 2) Fallback: download from HF Hub, then cache to LOCAL_IMAGE_MODEL
        try:
            if not IMAGE_MODEL_ID or "your-org/your-image-moderation-model" in IMAGE_MODEL_ID:
                raise RuntimeError(
                    "MODERATION_IMAGE_MODEL_ID is not set. Please set it in your .env "
                    "to a valid Hugging Face image model id."
                )

            logger.info(f"⬇️ Downloading image model from Hugging Face: {IMAGE_MODEL_ID}")
            # Let pipeline handle model/tokenizer/processor creation
            _image_pipeline = pipeline(
                task="image-classification",
                model=IMAGE_MODEL_ID,
                framework="pt",
                device=-1,
            )

            # Try to cache underlying model + processor locally
            try:
                os.makedirs(LOCAL_IMAGE_MODEL, exist_ok=True)
                _image_pipeline.model.save_pretrained(LOCAL_IMAGE_MODEL)

                if hasattr(_image_pipeline, "image_processor") and _image_pipeline.image_processor is not None:
                    _image_pipeline.image_processor.save_pretrained(LOCAL_IMAGE_MODEL)
                elif hasattr(_image_pipeline, "feature_extractor") and _image_pipeline.feature_extractor is not None:
                    _image_pipeline.feature_extractor.save_pretrained(LOCAL_IMAGE_MODEL)

                logger.info(f"💾 Image model cached at {LOCAL_IMAGE_MODEL}")
            except Exception as save_err:
                logger.warning(f"⚠️ Failed to cache image model locally: {save_err}")

            logger.info("✅ Remote image pipeline loaded successfully.")
            return _image_pipeline

        except Exception as e:
            err = f"❌ Failed to load image model (local and remote): {e}"
            logger.exception(err)
            raise RuntimeError(err) from e


# -------------------------
# Decision logic
# -------------------------
def decision_from_scores(labels: Dict[str, float]):
    # You can later plug in your thresholds here
    return "classification_only", labels


# -------------------------
# Celery task
# -------------------------
@celery_app.task(name="app.workers.tasks.process_moderation_task")
def process_moderation_task(job_id: int):
    db: Session = LocalSessionLocal()
    job = None
    try:
        job = crud.mark_job_processing(db, job_id)
        if not job:
            return {"error": "job not found", "job_id": job_id}

        logger.info(f"Processing job {job.id} (type={job.type})")

        if job.type == "text":
            # ---------------- TEXT ----------------
            try:
                pipe = _load_text_pipeline()
            except Exception as e:
                crud.update_job_result(
                    db,
                    job.id,
                    "needs_review",
                    {"error": str(e)},
                    notes="Model load failed",
                )
                return {"job_id": job.id, "error": str(e)}

            try:
                text = (job.data or "")[:10000]
                res = pipe(text)

                labels = {item["label"].lower(): float(item["score"]) for item in res[0]}
                decision, mapped = decision_from_scores(labels)

            except Exception as e:
                tb = traceback.format_exc()
                crud.update_job_result(
                    db,
                    job.id,
                    "needs_review",
                    {"error": str(e), "trace": tb},
                    notes="Pipeline error",
                )
                return {"job_id": job.id, "error": str(e)}

        elif job.type == "image":
            # ---------------- IMAGE (if you use it) ----------------
            try:
                pipe = _load_image_pipeline()
            except Exception as e:
                crud.update_job_result(
                    db,
                    job.id,
                    "needs_review",
                    {"error": str(e)},
                    notes="Image model load failed",
                )
                return {"job_id": job.id, "error": str(e)}

            try:
                # assuming job.data is base64-encoded image
                img_bytes = base64.b64decode(job.data)
                image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                res = pipe(image)

                labels = {item["label"].lower(): float(item["score"]) for item in res}
                decision, mapped = decision_from_scores(labels)

            except Exception as e:
                tb = traceback.format_exc()
                crud.update_job_result(
                    db,
                    job.id,
                    "needs_review",
                    {"error": str(e), "trace": tb},
                    notes="Image pipeline error",
                )
                return {"job_id": job.id, "error": str(e)}

        else:
            crud.update_job_result(
                db,
                job.id,
                "needs_review",
                {"error": "unknown type"},
                notes="Unknown job type",
            )
            return {"job_id": job.id, "error": "unknown type"}

        # Save final decision
        crud.update_job_result(db, job.id, decision, mapped, notes="Processed locally")
        return {"job_id": job.id, "decision": decision, "labels": mapped}

    except Exception as e:
        tb = traceback.format_exc()
        safe_id = job.id if job else job_id
        crud.update_job_result(
            db,
            safe_id,
            "needs_review",
            {"error": str(e), "trace": tb},
            notes="Unexpected error",
        )
        return {"job_id": safe_id, "error": str(e)}

    finally:
        db.close()


def enqueue_moderation_task(job_id: int):
    process_moderation_task.apply_async(args=(job_id,), queue="moderation_queue")
