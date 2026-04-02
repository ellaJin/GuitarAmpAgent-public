# app/service/auth_service.py
from uuid import uuid4
from fastapi import HTTPException
from app.dao import user_dao
from app.db import get_db_con  # 引入连接管理
from app.core.security import hash_password, verify_password
import json

def register_user(data):
    user_id = str(uuid4())
    email = data.email.lower().strip()
    pw_hash = hash_password(data.password)
    display_name = data.display_name

    # Service 层开启连接上下文
    with get_db_con() as conn:
        try:
            # 将 conn 传给 DAO
            user_dao.create_email_user(conn, user_id, email, pw_hash, display_name)
            return user_id
        except Exception as e:
            conn.rollback() # 出错回滚
            msg = str(e).lower()
            if "unique" in msg or "duplicate" in msg:
                raise HTTPException(status_code=400, detail="Email already registered")
            raise

def authenticate_user(data):
    email = data.email.lower().strip()

    with get_db_con() as conn:
        try:
            # 1. 通过 DAO 获取用户信息 (传入 conn)
            row = user_dao.get_user_by_email(conn, email)
            if not row:
                return None

            user_id, password_hash = str(row[0]), row[1]

            # 2. 业务逻辑校验
            if not password_hash or not verify_password(data.password, password_hash):
                return None

            # 3. 通过 DAO 更新登录时间 (传入 conn)
            user_dao.update_last_login(conn, user_id)

            # 只有这里成功了，整个事务才会由 get_db_con 自动 commit
            return user_id
        except Exception as e:
            conn.rollback()
            raise e


def get_current_user_info(user_id: str):
    with get_db_con() as conn:
        row = user_dao.get_user_with_active_device(conn, user_id)
        if not row:
            return None

        active_device = row[3]
        if isinstance(active_device, str):
            # 有些驱动会把 json_build_object 返回成字符串
            try:
                active_device = json.loads(active_device)
            except Exception:
                pass

        return {
            "id": row[0],
            "email": row[1],
            "display_name": row[2],
            "active_device": active_device,  # None 或 dict
        }