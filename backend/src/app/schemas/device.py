# app/schemas/device.py
from typing import Optional
from pydantic import BaseModel, Field


class ActiveDeviceContext(BaseModel):
    user_device_id: Optional[str] = Field(
        None, description="user_devices.id，用于设备切换或审计"
    )

    device_model_id: str = Field(
        ..., description="device_models.id，设备的唯一业务身份"
    )

    brand: str = Field(
        ..., description="设备品牌，例如 Mooer"
    )

    model: str = Field(
        ..., description="设备型号，例如 GE150 Pro"
    )

    kb_source_id: str = Field(
        ..., description="RAG 检索使用的知识源 ID"
    )

    nickname: Optional[str] = Field(
        None, description="用户给设备起的名字，可为空，仅用于展示"
    )
