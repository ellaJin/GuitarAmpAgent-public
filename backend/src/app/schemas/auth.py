# app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from app.schemas.device import ActiveDeviceContext

class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=6, max_length=128)

class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class MeResponse(BaseModel):
    id: str
    email: str
    display_name: str
    active_device: Optional[ActiveDeviceContext] = None