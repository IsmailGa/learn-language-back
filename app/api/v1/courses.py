from typing import Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select, func # Changed from sqlmodel.select to sqlalchemy.select, added func
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.models.course import Course, Unit, Lesson, Exercise, Character
from app.models.language import Language
from app.models.progress import UserProgress
from app.schemas.courses import CourseBase, CourseCreate, CourseUpdate, Course as CourseSchema, CourseWithUnits, UnitWithLessons, LessonWithExercises, ExerciseSchema, CharacterSchema, LanguageSchema

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("/languages", response_model=list[LanguageSchema])
async def list_languages(session: DbSession):
    """
    List all available languages.
    """
    result = await session.execute(select(Language))
    return result.scalars().all()


@router.get("", response_model=list[CourseSchema])
async def list_courses(
    session: DbSession,
    source_lang_id: Optional[UUID] = None,
    target_lang_id: Optional[UUID] = None
):
    """
    List available courses.
    """
    query = select(Course).where(Course.is_active == True).options(
        selectinload(Course.source_lang),
        selectinload(Course.target_lang)
    )
    if source_lang_id:
        query = query.where(Course.source_lang_id == source_lang_id)
    if target_lang_id:
        query = query.where(Course.target_lang_id == target_lang_id)
        
    result = await session.execute(query)
    courses = result.scalars().all()
    return courses


@router.get("/practice")
async def get_practice_exercises(session: DbSession) -> list[ExerciseSchema]:
    """
    Get 10 random exercises for practice mode.
    """
    # Simply get random exercises for now
    result = await session.execute(
        select(Exercise).order_by(func.random()).limit(10)
    )
    exercises = result.scalars().all()
    return exercises


@router.post("/practice/complete")
async def complete_practice(
    current_user: CurrentUser,
    session: DbSession,
) -> dict:
    """
    Complete practice and restore 1 heart.
    """
    xp_earned = 15 # Flat XP for practice
    
    # Update user XP
    current_user.xp += xp_earned
    
    # Restore 1 heart if not full
    if current_user.hearts < 5:
        current_user.hearts += 1
        
    session.add(current_user)
    await session.commit()
    
    return {
        "message": "Practice completed!",
        "xp_earned": xp_earned,
        "new_xp": current_user.xp,
        "new_hearts": current_user.hearts
    }


@router.get("/{course_id}")
async def get_course(course_id: UUID, session: DbSession) -> CourseWithUnits:
    """
    Get course details with units.
    """
    result = await session.execute(
        select(Course)
        .where(Course.id == course_id)
        .options(
            selectinload(Course.units),
            selectinload(Course.source_lang),
            selectinload(Course.target_lang)
        )
    )
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    return course


@router.get("/{course_id}/characters")
async def get_course_characters(course_id: UUID, session: DbSession) -> list[CharacterSchema]:
    """
    Get all alphabet characters for a specific course.
    """
    result = await session.execute(
        select(Character)
        .where(Character.course_id == course_id)
        .order_by(Character.order_index)
    )
    characters = result.scalars().all()
    
    return characters


@router.get("/{course_id}/units/{unit_id}")
async def get_unit(course_id: UUID, unit_id: UUID, session: DbSession) -> UnitWithLessons:
    """
    Get unit with lessons.
    """
    result = await session.execute(
        select(Unit)
        .where(Unit.id == unit_id, Unit.course_id == course_id)
        .options(selectinload(Unit.lessons))
    )
    unit = result.scalar_one_or_none()
    
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unit not found"
        )
    
    return unit


@router.get("/lessons/{lesson_id}")
async def get_lesson(lesson_id: UUID, session: DbSession) -> LessonWithExercises:
    """
    Get lesson with exercises.
    """
    result = await session.execute(
        select(Lesson)
        .where(Lesson.id == lesson_id)
        .options(selectinload(Lesson.exercises))
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    return lesson


@router.post("/lessons/{lesson_id}/complete")
async def complete_lesson(
    lesson_id: UUID,
    mistakes: int = 0,
    current_user: CurrentUser = None,
    session: DbSession = None,
) -> dict:
    """
    Mark lesson as complete and award XP.
    """
    # Get lesson
    result = await session.execute(
        select(Lesson).where(Lesson.id == lesson_id)
    )
    lesson = result.scalar_one_or_none()
    
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lesson not found"
        )
    
    # Check if already completed
    result = await session.execute(
        select(UserProgress).where(
            UserProgress.user_id == current_user.id,
            UserProgress.lesson_id == lesson_id,
        )
    )
    existing_progress = result.scalar_one_or_none()
    
    if existing_progress:
        # Already completed, no XP awarded
        return {"message": "Lesson already completed", "xp_earned": 0}
    
    # Create progress record
    xp_earned = lesson.xp_reward
    progress = UserProgress(
        user_id=current_user.id,
        lesson_id=lesson_id,
        xp_earned=xp_earned,
        mistakes=mistakes,
    )
    session.add(progress)
    
    # Update user XP (global)
    current_user.xp += xp_earned
    session.add(current_user)
    
    # Update per-course XP
    if current_user.current_course_id:
        from app.models.user_course import UserCourse
        uc_result = await session.execute(
            select(UserCourse).where(
                UserCourse.user_id == current_user.id,
                UserCourse.course_id == current_user.current_course_id
            )
        )
        user_course = uc_result.scalar_one_or_none()
        if user_course:
            user_course.xp += xp_earned
            session.add(user_course)
            
    await session.commit()
    
    return {
        "message": "Lesson completed!",
        "xp_earned": xp_earned,
        "new_xp": current_user.xp,
        "new_hearts": current_user.hearts
    }


@router.get("/progress/me")
async def get_my_progress(current_user: CurrentUser, session: DbSession) -> dict:
    """
    Get current user's learning progress.
    """
    result = await session.execute(
        select(UserProgress)
        .where(UserProgress.user_id == current_user.id)
        .options(selectinload(UserProgress.lesson))
    )
    progress = result.scalars().all()
    
    return {
        "total_lessons_completed": len(progress),
        "total_xp": current_user.xp,
        "progress": progress,
    }


