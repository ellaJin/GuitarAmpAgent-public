# app/routers/jobs.py
from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import get_current_user_id
from app.db import get_db_con
from app.dao import job_dao

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/{job_id}")
def get_job_status(job_id: str, user_id: str = Depends(get_current_user_id)):
    with get_db_con() as conn:
        job = job_dao.get_job(conn, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if str(job["user_id"]) != str(user_id):
        raise HTTPException(status_code=403, detail="Forbidden")

    return {
        "id": job["id"],
        "status": job["status"],
        "stage": job["stage"],
        "progress": job["progress"],
        "error": job["error"],
        "kb_source_id": job["kb_source_id"],
        "document_id": job["document_id"],
        "enrichment_status": job["enrichment_status"],
        "enrichment_total": job["enrichment_total"],
        "enrichment_done": job["enrichment_done"],
    }
