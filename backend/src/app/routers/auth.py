# app/router/auth.py
from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.auth import RegisterIn, LoginIn, TokenOut
from app.core.security import create_access_token
from app.service.google_auth_service import process_google_login
from app.service import auth_service
from app.core.auth import get_current_user_id

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut)
def register(data: RegisterIn):
    # service
    user_id = auth_service.register_user(data)
    return TokenOut(access_token=create_access_token(subject=user_id))


@router.post("/login", response_model=TokenOut)
def login(data: LoginIn):
    # service
    user_id = auth_service.authenticate_user(data)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenOut(access_token=create_access_token(subject=user_id))


# @router.get("/google", response_model=TokenOut)
# async def google_auth_callback(code: str):
#     #  Google service
#     user_id = await process_google_login(code)
#
#     if not user_id:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Google authentication failed"
#         )
#
#     return TokenOut(access_token=create_access_token(subject=user_id))


@router.get("/me")
def get_me(user_id: str = Depends(get_current_user_id)):
    user_info = auth_service.get_current_user_info(user_id)
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    return user_info