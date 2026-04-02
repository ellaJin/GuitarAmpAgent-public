from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse
import urllib.parse

from app.core.config import settings  # 确保你的 config.py 里有 Google 相关配置
from app.core.security import create_access_token
from app.service.google_auth_service import process_google_login

router = APIRouter(prefix="/auth/google", tags=["google_auth"])


@router.get("/login")
async def google_login():
    """
    发起 Google OAuth 登录流程
    """
    # 直接从 settings 获取，如果配置缺失，程序启动时就会报错，而不是等到现在
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_REDIRECT_URI:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google configuration missing in server settings"
        )

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "response_type": "code",
        "scope": "openid email profile",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "access_type": "offline",
        "prompt": "select_account"
    }

    google_auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    url = f"{google_auth_url}?{urllib.parse.urlencode(params)}"

    return RedirectResponse(url)


@router.get("/callback")
async def google_callback(code: str):
    """
    接收 Google 回调，处理用户登录/注册，并重定向回前端
    """
    try:
        # process_google_login 内部处理：去 Google 换取用户信息 -> 查库/创建用户 -> 返回 user_id
        user_id = await process_google_login(code)

        if not user_id:
            # 这里的失败通常是 Google Code 无效或网络问题
            return RedirectResponse(url="http://localhost:5173/login?error=google_auth_failed")

        # 生成系统内部使用的 JWT Token
        access_token = create_access_token(subject=str(user_id))

        # 重定向回前端页面。注意：token 放在 URL 参数中由前端解析
        # 建议前端地址也放入 settings 中，例如 settings.FRONTEND_URL
        frontend_callback_url = f"http://localhost:5173/auth-success?token={access_token}"

        return RedirectResponse(url=frontend_callback_url)

    except Exception as e:
        # 记录日志并跳转回登录页
        print(f"Google Login Error: {e}")
        return RedirectResponse(url="http://localhost:5173/login?error=server_error")