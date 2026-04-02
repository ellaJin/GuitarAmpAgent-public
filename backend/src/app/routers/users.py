from fastapi import APIRouter, Depends
from app.core.auth import get_current_user_id

router = APIRouter()

@router.get("/me")
def me(user=Depends(get_current_user_id)):
    return user
