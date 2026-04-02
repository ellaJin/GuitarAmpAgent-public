# app/schemas/chat.py
from typing import Any, List, Optional, Literal
from pydantic import BaseModel, Field
from app.schemas.device import ActiveDeviceContext


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]  # 你DB如果用 human/ai 也可以改这里
    content: str


class ChatQueryRequest(BaseModel):
    user_input: str = Field(..., min_length=1)
    chat_history: Optional[List[ChatMessage]] = None


class ChatQueryContext(BaseModel):
    user_id: str
    user_name: str
    active_device: Optional[ActiveDeviceContext]


class ChatQueryResponse(BaseModel):
    answer: str
