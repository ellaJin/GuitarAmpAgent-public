# app/router/device.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel
from app.service import device_service
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/devices", tags=["Device"])


class BindDeviceRequest(BaseModel):
    device_model_id: str


@router.get("/available")
def available_devices(current_user: dict = Depends(get_current_user_id)):
    """Return all admin-uploaded devices the user can select during onboarding."""
    return device_service.get_available_devices()


@router.post("/bind")
def bind_device(
    body: BindDeviceRequest,
    current_user: dict = Depends(get_current_user_id),
):
    """Bind the authenticated user to an existing admin-created device."""
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        return device_service.bind_user_to_system_device(user_id, body.device_model_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/my")
def my_devices(current_user: dict = Depends(get_current_user_id)):
    """Return all devices bound to the current user."""
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    return device_service.get_user_devices(user_id)


@router.post("/bind-inactive", status_code=201)
def bind_device_inactive(
    body: BindDeviceRequest,
    current_user: dict = Depends(get_current_user_id),
):
    """Add a device to the user's list without making it active."""
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        return device_service.bind_user_device_inactive(user_id, body.device_model_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/my/{user_device_id}/activate")
def activate_my_device(
    user_device_id: str,
    current_user: dict = Depends(get_current_user_id),
):
    """Swap the active device for the current user. Returns updated device list."""
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user
    try:
        return device_service.activate_user_device(user_id, user_device_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/activate")
async def activate(
        background_tasks: BackgroundTasks,
        brand: str = Form(...),
        model: str = Form(...),
        variant: str = Form(None),
        file: UploadFile = File(...),
        current_user: dict = Depends(get_current_user_id)
):
    # 获取用户 ID
    user_id = current_user["id"] if isinstance(current_user, dict) else current_user

    # 将文本数据封装，保持与你原有 Service 习惯一致
    device_info = {
        "brand": brand,
        "model": model,
        "variant": variant
    }

    # 调用新的 Service 处理函数
    return await device_service.activate_device_with_kb(
        user_id, device_info, file, background_tasks)