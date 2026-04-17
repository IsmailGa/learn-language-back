from fastapi import APIRouter, HTTPException, status
from sqlmodel import select

import logging
import uuid
from app.api.deps import DbSession
from app.core.config import settings
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

logger = logging.getLogger(__name__)


async def create_user(data: EmailRegisterRequest, session: DbSession) -> TokenResponse:
    """
    Register new user with email and password.
    """
    result = await session.execute(
        select(User).where(User.email == data.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        logger.warn("Email already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        email=data.email.lower(),
        hashed_password=security.get_password_hash(data.password),
        username=data.username,
        verification_token=str(uuid.uuid4())
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    from app.services.email import send_verification_email
    await send_verification_email(user.email, user.verification_token)
    
    
    token = security.create_access_token(user.id)
    return TokenResponse(access_token=token)

async def verify_email(token: str, session: DbSession):
    result = await session.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=400, detail="Invalid token")
        
    user.is_verified = True
    user.verification_token = None
    session.add(user)
    await session.commit()
    return True

async def login_via_google(data: GoogleLoginRequest, session: DbSession) -> TokenResponse:
    from google.oauth2 import id_token
    from google.auth.transport import requests
    
    try:
        id_info = id_token.verify_oauth2_token(
            data.credential, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Google token")

    email = id_info['email']
    
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            email=email,
            username=id_info.get('name'),
            avatar_url=id_info.get('picture'),
            is_verified=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
    token = security.create_access_token(user.id)
    return TokenResponse(access_token=token)

async def login_via_telegram(data: TelegramAuthRequest, session: DbSession) -> TelegramAuthResponse:
    """
    Telegram Registration Handler
    Authenticate user via Telegram Web App initData.
    Creates new user if not exists.
    """

    tg_user_data = security.verify_telegram_data(data.initData, settings.BOT_TOKEN)
    if not tg_user_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram data"
        )
    
    tg_id = tg_user_data["id"]
    
    result = await session.execute(
        select(User).where(User.telegram_id == tg_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=tg_id,
            username=tg_user_data.get("username") or tg_user_data.get("first_name"),
            avatar_url=tg_user_data.get("photo_url"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    token = security.create_access_token(user.id)

    return TelegramAuthResponse(access_token=token, user=user)


async def login_via_email(data: EmailLoginRequest, session: DbSession) -> TokenResponse:
    """
    Login with email and password.
    """
    result = await session.execute(
        select(User).where(User.email == data.email.lower())
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not security.verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    token = security.create_access_token(user.id)
    return TokenResponse(access_token=token)


async def login_via_telegram_widget(data: TelegramWidgetLoginRequest, session: DbSession) -> TelegramAuthResponse:
    """
    Telegram Login Widget Handler
    """
    # Verify data
    if not security.verify_telegram_widget_data(data.dict(exclude_none=True), settings.BOT_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Telegram data"
        )
    
    tg_id = data.id
    
    result = await session.execute(
        select(User).where(User.telegram_id == tg_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=tg_id,
            username=data.username or data.first_name,
            avatar_url=data.photo_url,
            is_verified=True # Telegram users are considered verified
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
    token = security.create_access_token(user.id)
    return TelegramAuthResponse(access_token=token, user=user)
