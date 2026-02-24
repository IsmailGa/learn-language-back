from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from uuid import UUID
from app.services.validation import PASSWORD_REGEX, USERNAME_REGEX

class TelegramAuthRequest(BaseModel):
    initData: str


class TelegramWidgetLoginRequest(BaseModel):
    id: int
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None
    photo_url: Optional[str] = None
    auth_date: int
    hash: str


class GoogleLoginRequest(BaseModel):
    credential: str


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower()


class EmailRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    username: str

    @validator("email")
    def email_to_lower(cls, v):
        return v.lower()
    @validator("username")
    def validate_username(cls, v):
        if not USERNAME_REGEX.match(v):
            raise ValueError("User name should consist of only letters, numbers and underscores, and should be between 3 and 20 characters long")
        return v
    
    @validator("password")
    def password_valid(cls, v):
        if not PASSWORD_REGEX.match(v):
            raise ValueError("Password too weak. It should contain at least one uppercase letter, one lowercase letter and one number.")
        return v

class UserResponse(BaseModel):
    id: UUID | str
    username: Optional[str]
    email: Optional[str]
    telegram_id: Optional[int]
    avatar_url: Optional[str]
    hearts: int
    xp: int
    streak: int
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    success: bool = True

class TelegramAuthResponse(BaseModel):
    access_token: str
    user: UserResponse
    token_type: str = "bearer"
    success: bool = True