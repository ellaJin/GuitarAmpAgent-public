# app/service/conversation_service.py
from app.db import get_db_con
from app.dao import conversation_dao


def start_or_continue(
    user_id: str,
    conversation_id: str,
    user_message: str,
    device_model_id: str = None,
) -> tuple:
    """
    Create or continue a conversation, then append the user message.

    Returns (conversation_id, user_message_id).
    If the supplied conversation_id is invalid/missing we silently create a new one.
    """
    title = (user_message[:57] + "...") if len(user_message) > 60 else user_message

    with get_db_con() as conn:
        if conversation_id:
            # Verify ownership — fall back to new conversation if not found
            row = conversation_dao.get_conversation_with_messages(
                conn, user_id, conversation_id
            )
            if row:
                conv_id = conversation_id
            else:
                conv_id = conversation_dao.create_conversation(
                    conn, user_id, title, device_model_id
                )
        else:
            conv_id = conversation_dao.create_conversation(
                conn, user_id, title, device_model_id
            )

        user_msg_id = conversation_dao.append_message(conn, conv_id, "user", user_message)
        conn.commit()

    return conv_id, user_msg_id


def save_ai_response(conversation_id: str, content: str) -> str:
    """Append the assistant message and bump conversation updated_at. Returns message_id."""
    with get_db_con() as conn:
        msg_id = conversation_dao.append_message(conn, conversation_id, "assistant", content)
        conversation_dao.touch_conversation(conn, conversation_id)
        conn.commit()
    return msg_id


def list_conversations(user_id: str) -> list:
    with get_db_con() as conn:
        return conversation_dao.get_conversations(conn, user_id)


def get_conversation(user_id: str, conversation_id: str):
    with get_db_con() as conn:
        return conversation_dao.get_conversation_with_messages(conn, user_id, conversation_id)


def update_title(user_id: str, conversation_id: str, title: str):
    with get_db_con() as conn:
        conversation_dao.update_conversation_title(conn, user_id, conversation_id, title)
        conn.commit()


def delete_conversation(user_id: str, conversation_id: str):
    with get_db_con() as conn:
        conversation_dao.delete_conversation(conn, user_id, conversation_id)
        conn.commit()
