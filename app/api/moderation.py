from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
# from app.db.database import get_real_db
from app.db.database import get_local_db
from app.db import crud
from app.workers.tasks import enqueue_moderation_task

# router = APIRouter()
router = APIRouter(prefix="/Moderation", tags=["Moderation"])

class ModerationCreateRequest(BaseModel):
    content_id: str
    type: str               # "text" or "image"
    subtype: Optional[str] = None
    data: str               # text content OR base64 image OR URL

class ModerationQueuedResponse(BaseModel):
    content_id: str
    status: str = "pending"
    message: str = "Moderation job queued"

class ModerationStatusResponse(BaseModel):
    content_id: str
    status: str
    decision: Optional[str] = None
    labels: Optional[Dict[str, Any]] = None
    worker_notes: Optional[str] = None

# @router.post("/moderation", response_model=ModerationQueuedResponse)
# def submit_moderation(req: ModerationCreateRequest, db: Session = Depends(get_real_db)):
#     existing = crud.get_job_by_content_id(db, req.content_id)
#     if existing:
#         return {"content_id": existing.content_id, "status": existing.status, "message": "Already exists"}
#     job = crud.create_moderation_job(db, req.content_id, req.type, req.subtype, req.data)
#     enqueue_moderation_task(job.id)
#     return {"content_id": job.content_id, "status": job.status, "message": "Moderation job queued"}

# @router.get("/moderation/{content_id}", response_model=ModerationStatusResponse)
# def get_moderation_status(content_id: str, db: Session = Depends(get_real_db)):
#     job = crud.get_job_by_content_id(db, content_id)
#     if not job:
#         raise HTTPException(status_code=404, detail="Job not found")
#     return {
#         "content_id": job.content_id,
#         "status": job.status,
#         "decision": job.decision,
#         "labels": job.labels,
#         "worker_notes": job.worker_notes,
#     }

@router.post("/moderation", response_model=ModerationQueuedResponse)
def submit_moderation(req: ModerationCreateRequest, db: Session = Depends(get_local_db)):
    existing = crud.get_job_by_content_id(db, req.content_id)
    if existing:
        return {"content_id": existing.content_id, "status": existing.status, "message": "Already exists"}
    job = crud.create_moderation_job(db, req.content_id, req.type, req.subtype, req.data)
    enqueue_moderation_task(job.id)
    return {"content_id": job.content_id, "status": job.status, "message": "Moderation job queued"}

@router.get("/moderation/{content_id}", response_model=ModerationStatusResponse)
def get_moderation_status(content_id: str, db: Session = Depends(get_local_db)):
    job = crud.get_job_by_content_id(db, content_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {
        "content_id": job.content_id,
        "status": job.status,
        "decision": job.decision,
        "labels": job.labels,
        "worker_notes": job.worker_notes,
    }
