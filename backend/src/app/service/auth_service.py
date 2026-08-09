# app/service/auth_service.py
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from fastapi import HTTPException
from app.dao import user_dao, pending_registration_dao, rate_limit_dao
from app.db import get_db_con  # 引入连接管理
from app.core.security import hash_password, verify_password
from app.service.email_service import send_verification_code, EmailSendError
import json

CODE_TTL_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60
MAX_ATTEMPTS = 5


def enforce_register_rate_limit(client_ip: str) -> None:
    with get_db_con() as conn:
        allowed = rate_limit_dao.check_and_increment(conn, client_ip)
    if allowed is None:
        raise HTTPException(
            status_code=429,
            detail="Too many registration requests from this address. Please try again later.",
        )


def _generate_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def request_verification_code(data):
    """Shared by initial signup and resend. Idempotent: never touches `users`."""
    email = data.email.lower().strip()
    now = datetime.now(timezone.utc)

    with get_db_con() as conn:
        if user_dao.get_user_by_email(conn, email):
            raise HTTPException(status_code=400, detail="Email already registered")

        pending = pending_registration_dao.get_pending_by_email(conn, email)
        if pending:
            created_at = pending[6]
            if now - created_at < timedelta(seconds=RESEND_COOLDOWN_SECONDS):
                return {"message": "A code was already sent. Please check your email."}

        code = _generate_code()
        code_hash = hash_password(code)
        pw_hash = hash_password(data.password)
        expires_at = now + timedelta(minutes=CODE_TTL_MINUTES)

        pending_registration_dao.upsert_pending(
            conn, email, data.display_name, pw_hash, code_hash, expires_at
        )
        # `with` exits cleanly here -> commits, before we ever call out to Resend.

    try:
        send_verification_code(email, code)
    except EmailSendError:
        # Pending row is already committed; don't roll it back. The user can
        # just call this same endpoint again to resend.
        raise HTTPException(
            status_code=502,
            detail="Failed to send verification email. Please try again.",
        )

    return {"message": "Verification code sent."}


def verify_registration_code(data):
    email = data.email.lower().strip()
    now = datetime.now(timezone.utc)

    with get_db_con() as conn:
        pending = pending_registration_dao.get_pending_by_email(conn, email)
        if not pending:
            raise HTTPException(status_code=400, detail="Request a code first.")

        _, display_name, password_hash, code_hash, expires_at, attempts, _ = pending

        if expires_at < now:
            raise HTTPException(status_code=400, detail="Code expired, request a new one.")

        if attempts >= MAX_ATTEMPTS:
            raise HTTPException(status_code=400, detail="Too many attempts, request a new one.")

        if not verify_password(data.code, code_hash):
            pending_registration_dao.increment_attempts(conn, email)
            # `raise` below propagates out of this `with` block, and psycopg's
            # Connection.__exit__ rolls back on any exception in flight -- so
            # the increment must be committed explicitly here, or it's lost
            # and MAX_ATTEMPTS never trips.
            conn.commit()
            raise HTTPException(status_code=400, detail="Incorrect code.")

        user_id = str(uuid4())
        user_dao.create_email_user(conn, user_id, email, password_hash, display_name)
        pending_registration_dao.delete_pending(conn, email)

    return user_id


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
