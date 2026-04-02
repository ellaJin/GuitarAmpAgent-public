# app/routers/conversations.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth import get_current_user_id
from app.service import conversation_service

router = APIRouter(prefix="/conversations", tags=["Conversations"])


class UpdateTitleRequest(BaseModel):
    title: str


@router.get("")
def list_conversations(user_id: str = Depends(get_current_user_id)):
    return conversation_service.list_conversations(user_id)


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    conv = conversation_service.get_conversation(user_id, conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@router.patch("/{conversation_id}")
def update_conversation(
    conversation_id: str,
    body: UpdateTitleRequest,
    user_id: str = Depends(get_current_user_id),
):
    conversation_service.update_title(user_id, conversation_id, body.title)
    return {"status": "ok"}


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    conversation_service.delete_conversation(user_id, conversation_id)
