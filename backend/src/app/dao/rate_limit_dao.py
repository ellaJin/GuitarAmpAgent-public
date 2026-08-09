# app/dao/rate_limit_dao.py

WINDOW_SECONDS = 15 * 60
MAX_REQUESTS = 10


def check_and_increment(conn, ip: str):
    """
    Atomic lazy-reset + gate + increment for the per-IP register rate
    limit -- same upsert-with-guard shape as the users quota UPDATE, so
    concurrent requests from the same IP can't slip past.
    Returns the new request_count on success, or None if this IP is
    already at the cap for the current window.
    """
    with conn.cursor() as cur:
        cur.execute(
            f"""
            INSERT INTO register_rate_limits (ip, window_start, request_count)
            VALUES (%s, now(), 1)
            ON CONFLICT (ip) DO UPDATE SET
                request_count = CASE
                    WHEN register_rate_limits.window_start <= now() - interval '{WINDOW_SECONDS} seconds'
                        THEN 1
                    ELSE register_rate_limits.request_count + 1
                END,
                window_start = CASE
                    WHEN register_rate_limits.window_start <= now() - interval '{WINDOW_SECONDS} seconds'
                        THEN now()
                    ELSE register_rate_limits.window_start
                END
            WHERE register_rate_limits.window_start <= now() - interval '{WINDOW_SECONDS} seconds'
               OR register_rate_limits.request_count < %s
            RETURNING request_count
            """,
            (ip, MAX_REQUESTS),
        )
        row = cur.fetchone()
        return row[0] if row else None
