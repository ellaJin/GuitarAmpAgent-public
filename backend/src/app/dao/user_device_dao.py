# app/dao/user_device_dao.py
from typing import List, Dict, Optional

def list_user_devices(conn, user_id: str) -> List[Dict]:
    sql = """
        SELECT
            ud.id AS user_device_id,
            ud.nickname,
            ud.is_active,
            dm.id AS device_model_id,
            dm.brand,
            dm.model,
            dm.variant
        FROM user_devices ud
        JOIN device_models dm ON dm.id = ud.device_model_id
        WHERE ud.user_id = %s
        ORDER BY ud.id DESC
    """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        rows = cur.fetchall() or []

    out: List[Dict] = []
    for r in rows:
        out.append({
            "user_device_id": r[0],
            "nickname": r[1],
            "is_active": r[2],
            "device_model_id": r[3],
            "brand": r[4],
            "model": r[5],
            "variant": r[6],
        })
    return out

def get_active_user_device(conn, user_id: str) -> Optional[Dict]:
    sql = """
        SELECT
            ud.id AS user_device_id,
            ud.nickname,
            ud.is_active,
            dm.id AS device_model_id,
            dm.brand,
            dm.model,
            dm.variant
        FROM user_devices ud
        JOIN device_models dm ON dm.id = ud.device_model_id
        WHERE ud.user_id = %s AND ud.is_active = TRUE
        ORDER BY ud.id DESC
        LIMIT 1
    """
    with conn.cursor() as cur:
        cur.execute(sql, (user_id,))
        r = cur.fetchone()

    if not r:
        return None

    return {
        "user_device_id": r[0],
        "nickname": (r[1] or None),
        "is_active": r[2],
        "device_model_id": r[3],
        "brand": r[4],
        "model": r[5],
        "variant": r[6],
    }
