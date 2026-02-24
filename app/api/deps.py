from datetime import datetime, timedelta
from typing import Annotated
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from jose import jwt, JWTError

from app.core.config import settings
from app.core.db import get_session
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> User:
    """
    Dependency to get current authenticated user from JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await session.execute(
        select(User).where(User.id == UUID(user_id))
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise credentials_exception
    
    # Heart Replenishment Logic (1 heart per hour)
    if user.hearts < 5:
        now = datetime.utcnow()
        elapsed = now - user.last_heart_refill_at
        hours_passed = int(elapsed.total_seconds() // 3600)
        
        if hours_passed > 0:
            user.hearts = min(5, user.hearts + hours_passed)
            # Advance the last refill time by exactly the number of hours passed
            # so fractional time isn't lost
            user.last_heart_refill_at = user.last_heart_refill_at + timedelta(hours=hours_passed)
            # If we hit 5 hearts, reset the timer to now
            if user.hearts == 5:
                 user.last_heart_refill_at = now
                 
            session.add(user)
            await session.commit()
    
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
DbSession = Annotated[AsyncSession, Depends(get_session)]
