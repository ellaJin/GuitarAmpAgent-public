# app/dao/pending_registration_dao.py

def get_pending_by_email(conn, email: str):
    """Fetch a pending registration row by email.
    Row order: email, display_name, password_hash, code_hash, expires_at, attempts, created_at
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT email, display_name, password_hash, code_hash, expires_at, attempts, created_at
            FROM pending_registrations
            WHERE email = %s
            """,
            (email,),
        )
        return cur.fetchone()


def upsert_pending(conn, email, display_name, password_hash, code_hash, expires_at):
    """Insert a new pending registration, or wholesale-overwrite an existing one
    (new password, new code, attempts reset to 0, created_at reset to now)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO pending_registrations
                (email, display_name, password_hash, code_hash, expires_at, attempts, created_at)
            VALUES (%s, %s, %s, %s, %s, 0, now())
            ON CONFLICT (email) DO UPDATE SET
                display_name  = EXCLUDED.display_name,
                password_hash = EXCLUDED.password_hash,
                code_hash     = EXCLUDED.code_hash,
                expires_at    = EXCLUDED.expires_at,
                attempts      = 0,
                created_at    = now()
            """,
            (email, display_name, password_hash, code_hash, expires_at),
        )


def increment_attempts(conn, email):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE pending_registrations SET attempts = attempts + 1 WHERE email = %s",
            (email,),
        )


def delete_pending(conn, email):
    with conn.cursor() as cur:
        cur.execute("DELETE FROM pending_registrations WHERE email = %s", (email,))
