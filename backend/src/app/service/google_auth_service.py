import httpx
from uuid import uuid4
from app.core.config import settings
from app.dao import user_dao
from app.db import get_db_con


async def fetch_google_user_info(code: str):
    """专门负责与 Google 打交道的函数"""
    async with httpx.AsyncClient() as client:
        # 1. 换取 Token
        token_res = await client.post("https://oauth2.googleapis.com/token", data={
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        })
        if token_res.status_code != 200:
            return None

        # 2. 获取用户信息
        access_token = token_res.json().get('access_token')
        user_info_res = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        return user_info_res.json() if user_info_res.status_code == 200 else None


async def process_google_login(code: str):
    """负责数据库逻辑编排"""
    # 1. 外部 API 调用 (不在事务锁内)
    google_data = await fetch_google_user_info(code)
    if not google_data:
        return None

    google_id = google_data.get("sub")
    email = google_data.get("email", "").lower().strip()
    username = google_data.get("name", "Google User")

    # 2. 数据库事务逻辑 (在事务锁内)
    with get_db_con() as conn:
        try:
            # 策略：Google ID 优先 -> Email 次之 -> 最后新建
            row = user_dao.get_user_by_google_id(conn, google_id)

            if row:
                user_id = str(row[0])
            else:
                row = user_dao.get_user_by_email(conn, email)
                if row:
                    user_id = str(row[0])
                    # 补充绑定 Google ID，防止下次用同一个 Google 号又找不到
                    user_dao.link_google_to_existing_user(conn, user_id, google_id)
                else:
                    user_id = str(uuid4())
                    # 注意：密码传 None 满足你的“不在库里就新建”需求
                    user_dao.create_google_user(conn, user_id, email, google_id, username)

            user_dao.update_last_login(conn, user_id)
            return user_id

        except Exception as e:
            # 这里通常 get_db_con 的上下文管理器会自动回滚，
            # 但如果你手动控制，conn.rollback() 也是安全的
            raise e