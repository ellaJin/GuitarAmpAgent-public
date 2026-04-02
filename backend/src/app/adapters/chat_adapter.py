# backend/src/app/adapters/chat_adapter.py
from typing import List, Optional, Any
from fastapi import HTTPException
from app.schemas.chat import ChatQueryRequest, ChatQueryContext, ChatMessage
from app.schemas.device import ActiveDeviceContext
from typing import Literal


Role = Literal["user", "assistant"]

def normalize_role(role: str) -> Role:
    r = (role or "").strip().lower()
    if r in ("user", "human"):
        return "user"
    if r in ("assistant", "ai"):
        return "assistant"
    raise HTTPException(status_code=400, detail=f"Invalid role: {role!r}")


def to_chat_messages(history: Optional[list]) -> Optional[List[ChatMessage]]:
    if not history:
        return None

    msgs: List[ChatMessage] = []
    for m in history:
        role = getattr(m, "role", None) if not isinstance(m, dict) else m.get("role")
        content = getattr(m, "content", None) if not isinstance(m, dict) else m.get("content")

        role_norm = normalize_role(role or "")

        if not isinstance(content, str):
            raise HTTPException(
                status_code=400,
                detail=f"History message content must be string, got {type(content).__name__}",
            )

        content = content.strip()
        if not content:
            raise HTTPException(status_code=400, detail="History message content is empty")

        msg = ChatMessage(role=role_norm, content=content)
        msgs.append(msg)

    return msgs or None




def to_chat_query_request(message: str, history: Optional[list] = None) -> ChatQueryRequest:
    """
    Build ChatQueryRequest from API payload:
    - message -> user_input
    - history -> chat_history (normalized ChatMessage list)
    """
    return ChatQueryRequest(
        user_input=message,
        chat_history=to_chat_messages(history),
    )


def to_chat_query_context(
    user_id: str,
    user_name: str,
    active_device: Optional[Any],
) -> ChatQueryContext:
    """
    Build ChatQueryContext for internal use.

    active_device must be:
    - None, or
    - dict (matching ActiveDeviceContext fields), or
    - ActiveDeviceContext instance

    IMPORTANT:
    - Do NOT pass stringified dict like "{'device_model_id':...}".
    - kb_source_id is carried inside active_device.kb_source_id (single source of truth).
    """

    if active_device is None:
        ad: Optional[ActiveDeviceContext] = None
    elif isinstance(active_device, ActiveDeviceContext):
        ad = active_device
    elif isinstance(active_device, dict):
        try:
            ad = ActiveDeviceContext(**active_device)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid active_device dict for ActiveDeviceContext: {type(e).__name__}: {e}",
            )
    else:
        raise HTTPException(
            status_code=500,
            detail=(
                "active_device must be dict/ActiveDeviceContext/None, "
                f"got {type(active_device).__name__}"
            ),
        )

    return ChatQueryContext(
        user_id=user_id,
        user_name=user_name,
        active_device=ad,
    )
