import psycopg
from app.core.config import settings

def get_db_con():
    if not settings.DB_URL:
        raise RuntimeError("DB_URL is not set")
    return psycopg.connect(settings.DB_URL)
