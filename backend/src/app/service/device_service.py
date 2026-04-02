# app/service/device_service.py
import os
import hashlib
from fastapi import BackgroundTasks

from app.db import get_db_con
from app.dao import device_dao
from app.dao import job_dao

from app.service.kb_ingestion_service import process_document_embedding_worker

UPLOAD_DIR = "uploads"


def get_available_devices() -> list[dict]:
    """Return devices that users can select during onboarding."""
    with get_db_con() as conn:
        return device_dao.get_available_devices(conn)


def bind_user_to_system_device(user_id: str, device_model_id: str) -> dict:
    """Bind user to an admin-created device and return binding info."""
    with get_db_con() as conn:
        try:
            result = device_dao.bind_user_to_system_device(conn, user_id, device_model_id)
            conn.commit()
            return {"status": "ok", **result}
        except Exception:
            conn.rollback()
            raise


def get_user_devices(user_id: str) -> list[dict]:
    """Return all devices bound to this user."""
    with get_db_con() as conn:
        return device_dao.get_user_devices(conn, user_id)


def bind_user_device_inactive(user_id: str, device_model_id: str) -> dict:
    """Add a device to the user's list without activating it."""
    with get_db_con() as conn:
        try:
            result = device_dao.bind_user_device_inactive(conn, user_id, device_model_id)
            conn.commit()
            return {"status": "ok", **result}
        except Exception:
            conn.rollback()
            raise


def activate_user_device(user_id: str, user_device_id: str) -> list[dict]:
    """Swap active device; returns updated device list."""
    with get_db_con() as conn:
        try:
            device_dao.activate_user_device(conn, user_id, user_device_id)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    return get_user_devices(user_id)




def _build_device_name(device_info: dict) -> str:
    """
    Use brand + model (+ variant) as a human-readable name for LLM context.
    """
    brand = (device_info.get("brand") or "").strip()
    model = (device_info.get("model") or "").strip()
    variant = (device_info.get("variant") or "").strip()

    name = f"{brand} {model}".strip()
    if variant and variant.lower() not in model.lower():
        name = f"{name} {variant}"

    return name or "Device"


async def activate_device_with_kb(user_id: str, device_info: dict, upload_file, background_tasks: BackgroundTasks):
    # 1) 保存文件
    content = await upload_file.read()
    file_hash = hashlib.md5(content).hexdigest()
    ext = os.path.splitext(upload_file.filename)[1]
    saved_name = f"{file_hash}{ext}"

    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    file_path = os.path.join(UPLOAD_DIR, saved_name)
    with open(file_path, "wb") as f:
        f.write(content)

    device_name = _build_device_name(device_info)

    # 2) 数据库事务处理：activate + create job（同一个事务里）
    with get_db_con() as conn:
        try:
            file_data = {
                "title": upload_file.filename,
                "file_name": saved_name,
                "file_type": upload_file.content_type,
                "hash": file_hash,
            }

            model_id, kb_source_id, document_id, user_device_id = device_dao.activate_full_setup(
                conn, user_id, device_info, file_data
            )

            # ✅ 新增：创建 ingestion job
            job_id = job_dao.create_job(conn, user_id, kb_source_id, document_id)

            # ✅ 关键：必须 commit，否则 job 查不到/状态更新看不见
            conn.commit()

            # 3) 后台任务：加 job_id（用于更新状态）
            background_tasks.add_task(
                process_document_embedding_worker,
                user_id,
                document_id,
                file_path,
                device_name,
                job_id,   # ✅ 新增
            )

            return {
                "status": "success",
                "job_id": job_id,  # ✅ 新增：前端未来用它轮询显示提示
                "device_model_id": model_id,
                "user_device_id": user_device_id,
                "kb_source_id": kb_source_id,
                "document_id": document_id,
                "message": "File uploaded, indexing in background",
            }

        except Exception as e:
            conn.rollback()
            if os.path.exists(file_path):
                os.remove(file_path)
            raise e



