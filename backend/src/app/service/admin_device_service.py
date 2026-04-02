# app/service/admin_device_service.py
import os
import hashlib
from fastapi import BackgroundTasks

from app.db import get_db_con
from app.dao import device_dao
from app.dao import job_dao
from app.dao import admin_device_dao
from app.service.kb_ingestion_service import process_document_embedding_worker

SYSTEM_USER_ID = "00000000-0000-0000-0000-000000000000"

UPLOAD_DIR = "uploads"
MANUAL_SUBDIR = "manuals"
IMAGE_SUBDIR = "device_images"

MANUAL_DIR = os.path.join(UPLOAD_DIR, MANUAL_SUBDIR)
IMAGE_DIR = os.path.join(UPLOAD_DIR, IMAGE_SUBDIR)

# Valid source_type values (must match strategy_router._EFFECT_PIPELINE_SOURCE_TYPES)
VALID_SOURCE_TYPES = {"effects_settings", "mixed", "user_manual"}


def _ensure_dir(path: str) -> None:
    """Create directory if it does not exist."""
    os.makedirs(path, exist_ok=True)


def _build_device_name(device_info: dict) -> str:
    """
    Build a human-readable device name from brand/model/variant.
    Used for downstream LLM context (e.g., effects extraction).
    """
    brand = (device_info.get("brand") or "").strip()
    model = (device_info.get("model") or "").strip()
    variant = (device_info.get("variant") or "").strip()

    name = f"{brand} {model}".strip()
    if variant and variant.lower() not in model.lower():
        name = f"{name} {variant}".strip()

    return name or "Device"


def _save_upload_bytes(content: bytes, original_filename: str, dst_dir: str) -> tuple[str, str, str]:
    """
    Save uploaded bytes to disk using md5 hash as filename.

    Returns:
        (absolute_file_path, saved_basename, md5_hash)
    """
    _ensure_dir(dst_dir)

    file_hash = hashlib.md5(content).hexdigest()
    ext = os.path.splitext(original_filename)[1]
    saved_basename = f"{file_hash}{ext}"

    abs_path = os.path.join(dst_dir, saved_basename)
    with open(abs_path, "wb") as f:
        f.write(content)

    return abs_path, saved_basename, file_hash


def _resolve_source_type(device_info: dict) -> str:
    """
    Resolve and validate source_type from device_info.
    Falls back to 'mixed' if missing or invalid.

    Valid values:
      - effects_settings: dedicated effect parameter PDF
      - mixed:            single PDF containing all content (default)
      - user_manual:      operation guide only, no effect list
    """
    raw = (device_info.get("source_type") or "").strip().lower()
    if raw in VALID_SOURCE_TYPES:
        return raw
    if raw:
        print(f"⚠️ Unknown source_type '{raw}', falling back to 'mixed'")
    return "mixed"

def get_system_devices():
    """
    Return all system devices with kb_sources and ingestion status.
    """
    with get_db_con() as conn:
        return admin_device_dao.list_system_devices(conn)


def get_job_status(job_id: str) -> dict:
    """
    Return ingestion job status for admin polling.
    """
    with get_db_con() as conn:
        job = job_dao.get_job(conn, job_id)
    if not job:
        return None
    return {
        "id":                job["id"],
        "status":            job["status"],
        "stage":             job["stage"],
        "progress":          job["progress"],
        "error":             job["error"],
        "kb_source_id":      job["kb_source_id"],
        "document_id":       job["document_id"],
        "enrichment_status": job["enrichment_status"],
        "enrichment_total":  job["enrichment_total"],
        "enrichment_done":   job["enrichment_done"],
        # MIDI enrichment — independent of effect enrichment
        "midi_enrichment_status": job["midi_enrichment_status"],
        "midi_enrichment_total":  job["midi_enrichment_total"],
    }

async def activate_device_with_system_kb(
    device_info: dict,
    manual_file,
    image_file,
    background_tasks: BackgroundTasks,
):
    """
    Admin-only path: upload a device manual (and optional image) into the system KB.

    Flow:
      1) Save manual + image to uploads/
      2) DB transaction: device_model + kb_source (reused per device) + document + job
      3) Trigger background ingestion worker by job_id
    """
    manual_path = None
    image_path = None

    # ---- 1) Save manual to uploads/manuals/ ----
    manual_bytes = await manual_file.read()
    manual_path, manual_saved_basename, manual_hash = _save_upload_bytes(
        manual_bytes, manual_file.filename, MANUAL_DIR
    )

    # Store as relative path so ingestion worker can resolve:
    # UPLOAD_DIR + file_name -> uploads/manuals/<hash>.pdf
    manual_file_name = f"{MANUAL_SUBDIR}/{manual_saved_basename}"

    # ---- 2) Save image to uploads/device_images/ (optional) ----
    image_url = None
    image_mime = None
    if image_file is not None:
        img_bytes = await image_file.read()
        image_path, image_saved_basename, _img_hash = _save_upload_bytes(
            img_bytes, image_file.filename, IMAGE_DIR
        )
        image_url = f"/static/{IMAGE_SUBDIR}/{image_saved_basename}"
        image_mime = image_file.content_type

    # Resolve and validate source_type before entering DB transaction
    source_type = _resolve_source_type(device_info)

    # ---- 3) DB transaction ----
    with get_db_con() as conn:
        try:
            manual_data = {
                "title": manual_file.filename,
                "file_name": manual_file_name,
                "file_type": manual_file.content_type,
                "content_hash": manual_hash,
                # Drives both pick_profile() and should_run_effect_pipeline() in worker
                "source_type": source_type,
            }

            device_model_id, kb_source_id, document_id = device_dao.admin_activate_full_setup(
                conn,
                system_user_id=SYSTEM_USER_ID,
                device_info=device_info,
                manual_data=manual_data,
                image_url=image_url,
                image_mime=image_mime,
            )

            job_id = job_dao.create_job(conn, SYSTEM_USER_ID, kb_source_id, document_id)
            conn.commit()

            # ---- 4) Trigger background ingestion (worker loads all context from DB) ----
            background_tasks.add_task(process_document_embedding_worker, job_id)

            return {
                "status": "success",
                "job_id": job_id,
                "device_model_id": device_model_id,
                "kb_source_id": kb_source_id,
                "document_id": document_id,
                "source_type": source_type,
                "image_url": image_url,
                "supports_midi":           device_info.get("supports_midi", False),
                "supports_snapshots":      device_info.get("supports_snapshots", False),
                "supports_command_center": device_info.get("supports_command_center", False),
                "message": "Admin uploaded. Indexing in background (system user).",
            }

        except Exception as e:
            conn.rollback()

            # Clean up saved files if DB transaction fails
            for path in [manual_path, image_path]:
                try:
                    if path and os.path.exists(path):
                        os.remove(path)
                except Exception:
                    pass

            raise e


async def add_document_to_device(
    device_model_id: str,
    manual_file,
    source_type_raw: str,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Add a new document to an already-existing system device.

    Flow:
      1) Save manual PDF to uploads/manuals/
      2) DB transaction: new kb_source + document (device_models row untouched)
      3) Create ingestion job + trigger background worker
    """
    # 1) Save manual
    manual_bytes = await manual_file.read()
    manual_path, manual_saved_basename, manual_hash = _save_upload_bytes(
        manual_bytes, manual_file.filename, MANUAL_DIR
    )
    manual_file_name = f"{MANUAL_SUBDIR}/{manual_saved_basename}"

    source_type = _resolve_source_type({"source_type": source_type_raw})

    # 2) DB transaction
    with get_db_con() as conn:
        try:
            manual_data = {
                "title":        manual_file.filename,
                "file_name":    manual_file_name,
                "file_type":    manual_file.content_type,
                "content_hash": manual_hash,
                "source_type":  source_type,
            }

            kb_source_id, document_id = admin_device_dao.add_document_to_device(
                conn,
                device_model_id=device_model_id,
                manual_data=manual_data,
            )

            job_id = job_dao.create_job(conn, SYSTEM_USER_ID, kb_source_id, document_id)
            conn.commit()

            # 3) Trigger background ingestion
            background_tasks.add_task(process_document_embedding_worker, job_id)

            return {
                "status":        "success",
                "job_id":        job_id,
                "kb_source_id":  kb_source_id,
                "document_id":   document_id,
                "source_type":   source_type,
                "message":       "Document added. Indexing in background.",
            }

        except Exception as e:
            conn.rollback()
            raise e


def unlink_source(device_model_id: str, kb_source_id: str) -> dict:
    """
    Cascade-delete all data for a kb_source from a system device.
    Physical PDF files are NOT deleted (by design).
    """
    with get_db_con() as conn:
        admin_device_dao.unlink_source(conn, device_model_id, kb_source_id)
        conn.commit()

    return {
        "status":                "success",
        "deleted_kb_source_id":  kb_source_id,
    }