# app/routers/admin_device.py
import os
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Header, HTTPException

from app.service import admin_device_service

router = APIRouter(prefix="/admin/devices", tags=["AdminDevice"])


def require_admin(x_admin_token: str | None):
    token = os.getenv("ADMIN_TOKEN")
    if token and x_admin_token != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.post("/activate")
async def admin_activate(
    background_tasks: BackgroundTasks,
    brand: str = Form(...),
    model: str = Form(...),
    variant: str = Form(None),
    source_type: str = Form("mixed"),
    supports_midi: str = Form("false"),
    supports_snapshots: str = Form("false"),
    supports_command_center: str = Form("false"),
    manual_file: UploadFile = File(...),
    image_file: UploadFile = File(None),
    x_admin_token: str | None = Header(None),
):
    require_admin(x_admin_token)

    def _parse_bool(v: str) -> bool:
        return (v or "").strip().lower() in ("true", "1", "yes")

    device_info = {
        "brand":                   brand,
        "model":                   model,
        "variant":                 variant,
        "source_type":             source_type,
        "supports_midi":           _parse_bool(supports_midi),
        "supports_snapshots":      _parse_bool(supports_snapshots),
        "supports_command_center": _parse_bool(supports_command_center),
    }

    return await admin_device_service.activate_device_with_system_kb(
        device_info=device_info,
        manual_file=manual_file,
        image_file=image_file,
        background_tasks=background_tasks,
    )


@router.get("/")
def list_admin_devices(x_admin_token: str | None = Header(None)):
    """
    Return all system devices with kb_sources and ingestion status.
    """
    require_admin(x_admin_token)
    return admin_device_service.get_system_devices()

@router.get("/jobs/{job_id}")
def get_admin_job_status(job_id: str, x_admin_token: str | None = Header(None)):
    require_admin(x_admin_token)
    job = admin_device_service.get_job_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{device_model_id}/documents")
async def add_device_document(
    device_model_id: str,
    background_tasks: BackgroundTasks,
    source_type: str = Form("mixed"),
    manual_file: UploadFile = File(...),
    x_admin_token: str | None = Header(None),
):
    """Add a new document to an existing system device."""
    require_admin(x_admin_token)
    try:
        return await admin_device_service.add_document_to_device(
            device_model_id=device_model_id,
            manual_file=manual_file,
            source_type_raw=source_type,
            background_tasks=background_tasks,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{device_model_id}/sources/{kb_source_id}")
def delete_device_source(
    device_model_id: str,
    kb_source_id: str,
    x_admin_token: str | None = Header(None),
):
    """Unlink a document source from a system device and cascade-delete all related data."""
    require_admin(x_admin_token)
    try:
        return admin_device_service.unlink_source(device_model_id, kb_source_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

