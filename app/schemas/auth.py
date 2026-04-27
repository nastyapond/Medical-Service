from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
import re


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(..., max_length=15)
    password: str = Field(..., max_length=128)
    role: str = "user"  # Default to user, admin can set to admin

    @validator('full_name')
    def validate_full_name(cls, v):
        if not v.strip():
            raise ValueError('ФИО не может быть пустым')
        return v.strip()

    @validator('phone')
    def validate_phone(cls, v):
        if not re.fullmatch(r'^\+\d{10,15}$', v):
            raise ValueError('Введите телефон в формате +71234567890')
        return v

    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 6:
            raise ValueError('Пароль должен содержать минимум 6 символов')
        if not any(char.isdigit() for char in v):
            raise ValueError('Пароль должен содержать хотя бы одну цифру')
        if not any(char.isupper() for char in v):
            raise ValueError('Пароль должен содержать хотя бы одну заглавную букву')
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    refresh_token: str