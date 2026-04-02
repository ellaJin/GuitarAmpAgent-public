# app/dao/song_dao.py
import json


def create_song(
    conn,
    user_id: str,
    name: str,
    raw_text: str,
    structured_config=None,
    device_model_id: str = None,
    message_id: str = None,
) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO songs
                (user_id, name, raw_text, structured_config, device_model_id, message_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                user_id,
                name,
                raw_text,
                json.dumps(structured_config) if structured_config is not None else None,
                device_model_id,
                message_id,
            ),
        )
        return str(cur.fetchone()[0])


def get_songs(conn, user_id: str) -> list:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.name, s.notes, dm.brand, dm.model, s.created_at, s.updated_at
            FROM songs s
            LEFT JOIN device_models dm ON dm.id = s.device_model_id
            WHERE s.user_id = %s
            ORDER BY s.created_at DESC
            """,
            (user_id,),
        )
        rows = cur.fetchall()
    return [
        {
            "id": str(r[0]),
            "name": r[1],
            "notes": r[2],
            "brand": r[3],
            "model": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "updated_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]


def get_song(conn, user_id: str, song_id: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT s.id, s.name, s.notes, s.raw_text, s.structured_config,
                   dm.brand, dm.model, s.created_at, s.updated_at
            FROM songs s
            LEFT JOIN device_models dm ON dm.id = s.device_model_id
            WHERE s.id = %s AND s.user_id = %s
            """,
            (song_id, user_id),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id": str(row[0]),
        "name": row[1],
        "notes": row[2],
        "raw_text": row[3],
        "structured_config": row[4],  # psycopg2 auto-parses JSONB to dict
        "brand": row[5],
        "model": row[6],
        "created_at": row[7].isoformat() if row[7] else None,
        "updated_at": row[8].isoformat() if row[8] else None,
    }


def update_song(conn, user_id: str, song_id: str, name: str = None, notes=None) -> bool:
    fields = []
    values = []
    if name is not None:
        fields.append("name = %s")
        values.append(name)
    if notes is not None:
        fields.append("notes = %s")
        values.append(notes)
    if not fields:
        return False
    fields.append("updated_at = NOW()")
    values.extend([song_id, user_id])
    with conn.cursor() as cur:
        cur.execute(
            f"UPDATE songs SET {', '.join(fields)} WHERE id = %s AND user_id = %s",
            values,
        )
        return cur.rowcount > 0


def delete_song(conn, user_id: str, song_id: str) -> bool:
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM songs WHERE id = %s AND user_id = %s",
            (song_id, user_id),
        )
        return cur.rowcount > 0
