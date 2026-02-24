from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from app.api.deps import CurrentUser, DbSession
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user's profile.
    """
    return UserResponse(
        id=str(current_user.id),
        username=current_user.username,
        email=current_user.email,
        telegram_id=current_user.telegram_id,
        avatar_url=current_user.avatar_url,
        hearts=current_user.hearts,
        xp=current_user.xp,
        streak=current_user.streak,
    )


@router.post("/me/refill-hearts")
async def refill_hearts(current_user: CurrentUser, session: DbSession):
    """
    Refill user's hearts (max 5).
    In a real app, this would check time elapsed or use premium currency.
    """
    current_user.hearts = 5
    current_user.last_heart_refill_at = datetime.utcnow()
    session.add(current_user)
    await session.commit()
    
    return {"hearts": current_user.hearts}


@router.post("/me/hearts/deduct")
async def deduct_heart(current_user: CurrentUser, session: DbSession):
    """
    Deduct 1 heart from the user. Returns 400 if user has 0 hearts.
    """
    if current_user.hearts <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hearts left"
        )
        
    # If hitting 4 hearts from 5, start the refill timer
    if current_user.hearts == 5:
        current_user.last_heart_refill_at = datetime.utcnow()
        
    current_user.hearts -= 1
    session.add(current_user)
    await session.commit()
    
    return {"hearts": current_user.hearts}
