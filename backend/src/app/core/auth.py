# app/core/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.core.config import settings

bearer = HTTPBearer()

def get_current_user_id(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> str:
    token = cred.credentials
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        return str(user_id)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
