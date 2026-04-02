from fastapi import APIRouter
from app.core.db import get_db_conn

router = APIRouter()

@router.get("/health")
def health():
    info = {"status": "ok"}

    try:
        conn = get_db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                _ = cur.fetchone()
            info["db"] = "ok"
        finally:
            conn.close()
    except Exception as e:
        info["db"] = "error"
        info["db_error"] = str(e)

    return info
