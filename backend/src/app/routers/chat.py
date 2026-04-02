# backend/src/app/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional

from app.core.auth import get_current_user_id
from app.service.auth_service import get_current_user_info
from app.service import chat_service
from app.service import conversation_service
from app.adapters.chat_adapter import to_chat_query_request, to_chat_query_context

router = APIRouter(prefix="/chat", tags=["Chat"])


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[Message] = Field(default_factory=list)
    conversation_id: Optional[str] = None


@router.post("/query")
async def chat_query(
    request: ChatRequest,
    user_id: str = Depends(get_current_user_id),
):
    # 1) Look up user info (active device + display name)
    user_info = get_current_user_info(user_id)
    if not user_info:
        raise HTTPException(status_code=404, detail="用户信息不存在")

    active_device = user_info.get("active_device")
    if not active_device:
        raise HTTPException(status_code=403, detail="您尚未激活任何效果器设备，请先完成设备激活。")

    print("[chat] user_id =", user_id)
    print("[chat] active_device =", active_device)
    print("[chat] kb_source_id =", (active_device or {}).get("kb_source_id"))

    # 2) Persist user message and resolve conversation_id (before LLM call)
    device_model_id = (active_device or {}).get("device_model_id")
    conv_id = request.conversation_id
    try:
        conv_id, _ = conversation_service.start_or_continue(
            user_id, request.conversation_id, request.message, device_model_id
        )
    except Exception as e:
        print(f"[chat] persistence error (start): {e}")

    # 3) Adapter: API → internal standard req/ctx
    req = to_chat_query_request(request.message, request.history)
    ctx = to_chat_query_context(
        user_id=user_id,
        user_name=user_info.get("display_name") or user_info.get("email") or "User",
        active_device=active_device,
    )

    # 4) Call chat service (unchanged, fully stateless)
    answer = await chat_service.get_chat_response(req, ctx)

    # 5) Persist AI response
    ai_msg_id = None
    if conv_id:
        try:
            ai_msg_id = conversation_service.save_ai_response(conv_id, answer)
        except Exception as e:
            print(f"[chat] persistence error (ai_response): {e}")

    return {
        "answer": answer,
        "device": active_device,
        "status": "success",
        "conversation_id": conv_id,
        "ai_message_id": ai_msg_id,
    }
