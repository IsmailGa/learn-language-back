from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

from app.api.deps import DbSession
from app.core.config import settings
from app.crud.users import create_user, login_via_telegram, login_via_email, login_via_telegram_widget
from app.core import security
from app.models.user import User
from app.schemas.auth import (
    TelegramAuthRequest,
    EmailLoginRequest,
    EmailRegisterRequest,
    TokenResponse,
    TelegramAuthResponse,
    TelegramWidgetLoginRequest,
    GoogleLoginRequest
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=TelegramAuthResponse)
async def auth_telegram(data: TelegramAuthRequest, session: DbSession):
    """
    Authenticate user via Telegram Web App initData.
    Creates new user if not exists.
    """
    return await login_via_telegram(data, session)


@router.post("/telegram/widget", response_model=TelegramAuthResponse)
async def auth_telegram_widget(data: TelegramWidgetLoginRequest, session: DbSession):
    """
    Authenticate user via Telegram Login Widget.
    """
    return await login_via_telegram_widget(data, session)


@router.post("/register", response_model=TokenResponse)
async def register_email(data: EmailRegisterRequest, session: DbSession):
    """
    Register new user with email and password.
    """

    return await create_user(data, session)


@router.post("/login", response_model=TokenResponse)
async def login_email(data: EmailLoginRequest, session: DbSession):
    """
    Login with email and password.
    """

    return await login_via_email(data, session)


@router.post("/verify-email")
async def verify_email_endpoint(token: str, session: DbSession):
    from app.crud.users import verify_email
    await verify_email(token, session)
    return {"message": "Email verified successfully"}


@router.post("/callback/google", response_model=TokenResponse)
async def auth_google(data: GoogleLoginRequest, session: DbSession):
    from app.crud.users import login_via_google
    return await login_via_google(data, session)