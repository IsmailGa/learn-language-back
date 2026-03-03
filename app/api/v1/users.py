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
        current_course_id=current_user.current_course_id,
    )


@router.post("/me/select-course")
async def select_course(
    course_id: str,
    current_user: CurrentUser,
    session: DbSession
):
    """
    Select current course for the user.
    """
    from sqlalchemy import select
    from app.models.user_course import UserCourse
    from uuid import UUID
    
    try:
        course_uuid = UUID(course_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid course ID"
        )
    
    # Check if course exists
    from app.models.course import Course
    course_exists = await session.execute(select(Course).where(Course.id == course_uuid))
    if not course_exists.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
        
    current_user.current_course_id = course_uuid
    session.add(current_user)
    
    # Ensure UserCourse entry exists
    user_course_result = await session.execute(
        select(UserCourse).where(
            UserCourse.user_id == current_user.id,
            UserCourse.course_id == course_uuid
        )
    )
    user_course = user_course_result.scalar_one_or_none()
    
    if not user_course:
        user_course = UserCourse(
            user_id=current_user.id,
            course_id=course_uuid
        )
        session.add(user_course)
    
    await session.commit()
    
    return {"message": "Course selected successfully", "current_course_id": str(course_uuid)}

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
