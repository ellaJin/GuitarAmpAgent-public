# app/dao/user_dao.py
from datetime import datetime, timezone

def get_user_by_google_id(conn, google_id: str):
    """根据 Google ID 查询用户"""
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE google_id = %s", (google_id,))
        return cur.fetchone()

def get_user_by_email(conn, email: str):
    """根据 Email 查询用户"""
    with conn.cursor() as cur:
        cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
        return cur.fetchone()

def create_google_user(conn, user_id, email, google_id, display_name):
    """创建全新的 Google 用户"""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO users (id, email, google_id, display_name) VALUES (%s, %s, %s, %s)",
            (user_id, email, google_id, display_name),
        )

def create_email_user(conn, user_id, email, pw_hash, display_name):
    """创建普通的邮箱注册用户"""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users (id, email, password_hash, display_name)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, email, pw_hash, display_name),
        )

def link_google_to_existing_user(conn, user_id, google_id):
    """将 Google ID 绑定到现有邮箱账号"""
    with conn.cursor() as cur:
        cur.execute("UPDATE users SET google_id = %s WHERE id = %s", (google_id, user_id))

def update_last_login(conn, user_id):
    """更新最后登录时间"""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET last_login_at = %s WHERE id = %s",
            (datetime.now(timezone.utc), user_id),
        )

def get_user_with_active_device(conn, user_id: str):
    """
    查询用户信息及其激活设备的上下文（用于 RAG）
    - active_device: None 或 dict（包含 kb_source_id/device_model_id/brand/model/nickname）
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                u.id,
                u.email,
                u.display_name,
                CASE
                    WHEN ud.id IS NULL THEN NULL
                    ELSE json_build_object(
                        'user_device_id', ud.id,
                        'device_model_id', dm.id,
                        'brand', dm.brand,
                        'model', dm.model,
                        'kb_source_id', ks.id,
                        'nickname', ud.nickname
                    )
                END AS active_device
            FROM users u
            LEFT JOIN user_devices ud
              ON ud.user_id = u.id AND ud.is_active = TRUE
            LEFT JOIN device_models dm
              ON dm.id = ud.device_model_id
            LEFT JOIN kb_sources ks
              ON ks.id = ud.kb_source_id
            WHERE u.id = %s
            LIMIT 1
            """,
            (user_id,),
        )
        return cur.fetchone()


def check_and_increment_query(conn, user_id: str):
    """
    Atomic lazy-reset + gate + increment for the daily usage quota. If
    quota_date isn't today, resets both counters and allows the query
    unconditionally; otherwise requires both counts under their limits.
    Returns the new query_count on success, or None if over quota.
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE users
            SET query_count = CASE WHEN quota_date = current_date THEN query_count + 1 ELSE 1 END,
                token_count = CASE WHEN quota_date = current_date THEN token_count ELSE 0 END,
                quota_date  = current_date
            WHERE id = %s
              AND (quota_date <> current_date
                   OR (query_count < daily_query_limit AND token_count < daily_token_limit))
            RETURNING query_count
            """,
            (user_id,),
        )
        row = cur.fetchone()
        return row[0] if row else None


def get_quota_status(conn, user_id: str):
    """Snapshot for an over-quota error message: both caps, both current
    counts, and the DB's own notion of the next reset instant."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT daily_query_limit, daily_token_limit, query_count, token_count,
                   (current_date + 1)::timestamptz AS resets_at
            FROM users
            WHERE id = %s
            """,
            (user_id,),
        )
        return cur.fetchone()


def add_token_usage(conn, user_id: str, tokens: int) -> None:
    """Credit actual token usage after a completed LLM call. Not gated --
    the gate already happened in check_and_increment_query before the call."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET token_count = token_count + %s WHERE id = %s",
            (tokens, user_id),
        )


def decrement_query_count(conn, user_id: str) -> None:
    """Refund a query slot after a failed query, floored at 0 so a
    concurrent lazy reset (quota_date rolled over mid-request) can't push
    the count negative."""
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE users SET query_count = GREATEST(query_count - 1, 0) WHERE id = %s",
            (user_id,),
        )