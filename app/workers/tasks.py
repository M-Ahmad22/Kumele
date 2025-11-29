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
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline, Pipeline
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
    weight_candidates = {"pytorch_model.bin", "model.safetensors", "tf_model.h5", "flax_model.msgpack"}
    if not (present_files & weight_candidates):
        raise FileNotFoundError(
            f"No model weights found in {folder}. Expect one of: {', '.join(weight_candidates)}."
        )

    if "config.json" not in present_files:
        raise FileNotFoundError(f"Missing config.json in {folder}.")


# -------------------------
# Load text pipeline properly
# -------------------------
def _load_text_pipeline() -> Pipeline:
    global _text_pipeline
    if _text_pipeline is not None:
        return _text_pipeline

    with _pipeline_lock:
        if _text_pipeline is not None:
            return _text_pipeline

        try:
            _check_model_folder(LOCAL_TEXT_MODEL)
            logger.info(f"Loading local text model from {LOCAL_TEXT_MODEL}")

            model = AutoModelForSequenceClassification.from_pretrained(
                LOCAL_TEXT_MODEL,
                local_files_only=True
            )
            tokenizer = AutoTokenizer.from_pretrained(
                LOCAL_TEXT_MODEL,
                local_files_only=True
            )

            _text_pipeline = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer,
                top_k=None,  # ✅ replaces deprecated return_all_scores=True
                device=-1    # ✅ ensures CPU
            )

            logger.info("✅ Local text pipeline loaded successfully.")
            return _text_pipeline

        except Exception as e:
            err = f"❌ Failed to load local text model: {e}"
            logger.exception(err)
            raise RuntimeError(err) from e


# -------------------------
# (Optional) image model load
# -------------------------
def _load_image_pipeline() -> Pipeline:
    global _image_pipeline
    if _image_pipeline is not None:
        return _image_pipeline

    with _pipeline_lock:
        if _image_pipeline is not None:
            return _image_pipeline

        try:
            _check_model_folder(LOCAL_IMAGE_MODEL)
            logger.info(f"Loading local image model from {LOCAL_IMAGE_MODEL}")

            _image_pipeline = pipeline(
                task="image-classification",
                model=LOCAL_IMAGE_MODEL,
                framework="pt",
                device=-1,
                local_files_only=True
            )
            logger.info("✅ Local image pipeline loaded successfully.")
            return _image_pipeline

        except Exception as e:
            err = f"❌ Failed to load local image model: {e}"
            logger.exception(err)
            raise RuntimeError(err) from e


# -------------------------
# Decision logic
# -------------------------
def decision_from_scores(labels: Dict[str, float]):
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
            try:
                pipe = _load_text_pipeline()
            except Exception as e:
                crud.update_job_result(db, job.id, "needs_review", {"error": str(e)}, notes="Model load failed")
                return {"job_id": job.id, "error": str(e)}

            try:
                text = (job.data or "")[:10000]
                res = pipe(text)

                labels = {item["label"].lower(): float(item["score"]) for item in res[0]}
                decision, mapped = decision_from_scores(labels)

            except Exception as e:
                tb = traceback.format_exc()
                crud.update_job_result(db, job.id, "needs_review", {"error": str(e), "trace": tb}, notes="Pipeline error")
                return {"job_id": job.id, "error": str(e)}

        else:
            crud.update_job_result(db, job.id, "needs_review", {"error": "unknown type"}, notes="Unknown job type")
            return {"job_id": job.id, "error": "unknown type"}

        crud.update_job_result(db, job.id, decision, mapped, notes="Processed locally")
        return {"job_id": job.id, "decision": decision, "labels": mapped}

    except Exception as e:
        tb = traceback.format_exc()
        safe_id = job.id if job else job_id
        crud.update_job_result(db, safe_id, "needs_review", {"error": str(e), "trace": tb}, notes="Unexpected error")
        return {"job_id": safe_id, "error": str(e)}

    finally:
        db.close()


def enqueue_moderation_task(job_id: int):
    process_moderation_task.apply_async(args=(job_id,), queue="moderation_queue")
