# app/routers/songs.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.core.auth import get_current_user_id
from app.service import song_service

router = APIRouter(prefix="/songs", tags=["Songs"])


class CreateSongRequest(BaseModel):
    raw_text: str
    name: Optional[str] = None
    message_id: Optional[str] = None
    device_model_id: Optional[str] = None


class UpdateSongRequest(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None


@router.post("", status_code=201)
def create_song(
    body: CreateSongRequest,
    user_id: str = Depends(get_current_user_id),
):
    return song_service.create_song(
        user_id,
        raw_text=body.raw_text,
        name=body.name,
        message_id=body.message_id,
        device_model_id=body.device_model_id,
    )


@router.get("")
def list_songs(user_id: str = Depends(get_current_user_id)):
    return song_service.list_songs(user_id)


@router.get("/{song_id}")
def get_song(song_id: str, user_id: str = Depends(get_current_user_id)):
    song = song_service.get_song(user_id, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


@router.patch("/{song_id}")
def update_song(
    song_id: str,
    body: UpdateSongRequest,
    user_id: str = Depends(get_current_user_id),
):
    song = song_service.update_song(user_id, song_id, name=body.name, notes=body.notes)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


@router.delete("/{song_id}", status_code=204)
def delete_song(song_id: str, user_id: str = Depends(get_current_user_id)):
    deleted = song_service.delete_song(user_id, song_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Song not found")
