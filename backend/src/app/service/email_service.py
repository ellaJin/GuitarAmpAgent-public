# app/service/email_service.py
import httpx
from app.core.config import settings

RESEND_URL = "https://api.resend.com/emails"


class EmailSendError(Exception):
    """Raised when the Resend API call fails."""


def send_verification_code(to: str, code: str) -> None:
    """Send a 6-digit verification code to `to` via the Resend API."""
    if not settings.RESEND_API_KEY:
        raise EmailSendError("RESEND_API_KEY is not configured")

    resp = httpx.post(
        RESEND_URL,
        headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}"},
        json={
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to],
            "subject": "Your verification code",
            "text": f"Your verification code is {code}. It expires in 10 minutes.",
        },
        timeout=10.0,
    )
    if resp.status_code >= 400:
        raise EmailSendError(f"Resend API error {resp.status_code}: {resp.text}")
