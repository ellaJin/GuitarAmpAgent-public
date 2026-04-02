# app/dao/conversation_dao.py


def create_conversation(conn, user_id: str, title: str, device_model_id: str = None) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO conversations (user_id, title, device_model_id)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (user_id, title, device_model_id),
        )
        return str(cur.fetchone()[0])


def get_conversations(conn, user_id: str, limit: int = 50) -> list:
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                c.id,
                c.title,
                c.device_model_id,
                dm.brand,
                dm.model,
                c.created_at,
                c.updated_at,
                COUNT(m.id) AS message_count
            FROM conversations c
            LEFT JOIN device_models dm ON dm.id = c.device_model_id
            LEFT JOIN messages m ON m.conversation_id = c.id
            WHERE c.user_id = %s
            GROUP BY c.id, dm.brand, dm.model
            ORDER BY c.updated_at DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        rows = cur.fetchall()
    return [
        {
            "id": str(r[0]),
            "title": r[1],
            "device_model_id": str(r[2]) if r[2] else None,
            "brand": r[3],
            "model": r[4],
            "created_at": r[5].isoformat() if r[5] else None,
            "updated_at": r[6].isoformat() if r[6] else None,
            "message_count": int(r[7]),
        }
        for r in rows
    ]


def get_conversation_with_messages(conn, user_id: str, conversation_id: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT c.id, c.title, c.device_model_id, dm.brand, dm.model,
                   c.created_at, c.updated_at
            FROM conversations c
            LEFT JOIN device_models dm ON dm.id = c.device_model_id
            WHERE c.id = %s AND c.user_id = %s
            """,
            (conversation_id, user_id),
        )
        row = cur.fetchone()
        if not row:
            return None

        conv = {
            "id": str(row[0]),
            "title": row[1],
            "device_model_id": str(row[2]) if row[2] else None,
            "brand": row[3],
            "model": row[4],
            "created_at": row[5].isoformat() if row[5] else None,
            "updated_at": row[6].isoformat() if row[6] else None,
        }

        cur.execute(
            """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        )
        msgs = cur.fetchall()

    conv["messages"] = [
        {
            "id": str(m[0]),
            "role": m[1],
            "content": m[2],
            "created_at": m[3].isoformat() if m[3] else None,
        }
        for m in msgs
    ]
    return conv


def update_conversation_title(conn, user_id: str, conversation_id: str, title: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE conversations
            SET title = %s, updated_at = NOW()
            WHERE id = %s AND user_id = %s
            """,
            (title, conversation_id, user_id),
        )


def delete_conversation(conn, user_id: str, conversation_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM conversations WHERE id = %s AND user_id = %s",
            (conversation_id, user_id),
        )


def append_message(conn, conversation_id: str, role: str, content: str) -> str:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (conversation_id, role, content),
        )
        return str(cur.fetchone()[0])


def touch_conversation(conn, conversation_id: str):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE conversations SET updated_at = NOW() WHERE id = %s",
            (conversation_id,),
        )
