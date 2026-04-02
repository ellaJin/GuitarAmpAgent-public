# app/service/song_service.py
from app.db import get_db_con
from app.dao import song_dao
from app.dao import device_dao


def create_song(
    user_id: str,
    raw_text: str,
    name: str = None,
    message_id: str = None,
    device_model_id: str = None,
) -> dict:
    if not name:
        words = raw_text.strip().split()
        name = " ".join(words[:6]) + ("..." if len(words) > 6 else "")

    with get_db_con() as conn:
        # Auto-resolve active device if not explicitly provided
        if not device_model_id:
            device_model_id = device_dao.get_active_device_model_id(conn, user_id)

        song_id = song_dao.create_song(
            conn,
            user_id=user_id,
            name=name,
            raw_text=raw_text,
            structured_config=None,
            device_model_id=device_model_id,
            message_id=message_id,
        )
        conn.commit()

    return get_song(user_id, song_id)


def list_songs(user_id: str) -> list:
    with get_db_con() as conn:
        return song_dao.get_songs(conn, user_id)


def get_song(user_id: str, song_id: str):
    with get_db_con() as conn:
        return song_dao.get_song(conn, user_id, song_id)


def update_song(user_id: str, song_id: str, name: str = None, notes: str = None):
    with get_db_con() as conn:
        updated = song_dao.update_song(conn, user_id, song_id, name=name, notes=notes)
        if updated:
            conn.commit()
    return get_song(user_id, song_id)


def delete_song(user_id: str, song_id: str) -> bool:
    with get_db_con() as conn:
        deleted = song_dao.delete_song(conn, user_id, song_id)
        if deleted:
            conn.commit()
    return deleted
