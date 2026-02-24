import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.getcwd())

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.db import async_session_maker
from app.models.course import Course, Unit, Lesson, Exercise

async def seed_db():
    async with async_session_maker() as session:
        # Check if course already exists to avoid duplicates
        result = await session.execute(select(Course).where(Course.title == "Корейский"))
        existing_course = result.scalar_one_or_none()
        if existing_course:
            print("Course already exists. Deleting its dependencies to re-seed...")
            # We explicitly delete to avoid FK constraint issues if no cascade is set
            units_res = await session.execute(select(Unit).where(Unit.course_id == existing_course.id))
            units = units_res.scalars().all()
            for unit in units:
                lessons_res = await session.execute(select(Lesson).where(Lesson.unit_id == unit.id))
                lessons = lessons_res.scalars().all()
                for lesson in lessons:
                    # Delete exercises first
                    await session.execute(Exercise.__table__.delete().where(Exercise.lesson_id == lesson.id))
                    # Then delete lesson
                    await session.delete(lesson)
                # Delete unit
                await session.delete(unit)
            
            # Finally delete course
            await session.delete(existing_course)
            await session.flush()
            print("Deleted existing 'Корейский' course to re-seed.")

        # Create Course
        course = Course(
            title="Корейский",
            description="Базовый курс корейского языка",
            source_lang="ru",
            target_lang="ko",
            is_active=True
        )
        session.add(course)
        await session.flush() # To get the course.id

        # Create Units
        units_data = [
            {
                "title": "Хангыль",
                "description": "Алфавит и чтение",
                "order_index": 0,
                "lessons": [
                    {"title": "Гласные", "description": "Базовые гласные звуки", "xp_reward": 10, "order_index": 0},
                    {"title": "Согласные", "description": "Базовые согласные звуки", "xp_reward": 10, "order_index": 1},
                    {"title": "Слоги", "description": "Составление слогов", "xp_reward": 15, "order_index": 2}
                ]
            },
            {
                "title": "Приветствия",
                "description": "Знакомство и базовые фразы",
                "order_index": 1,
                "lessons": [
                    {"title": "Здравствуйте", "description": "Формальные приветствия", "xp_reward": 10, "order_index": 0},
                    {"title": "Как дела?", "description": "Повседневные выражения", "xp_reward": 10, "order_index": 1}
                ]
            },
            {
                "title": "Числа",
                "description": "Счет и цены",
                "order_index": 2,
                "lessons": [
                    {"title": "Корейские числительные", "description": "От 1 до 99", "xp_reward": 15, "order_index": 0},
                    {"title": "Китайские числительные", "description": "Деньги, даты и минуты", "xp_reward": 15, "order_index": 1}
                ]
            }
        ]

        for u_data in units_data:
            unit = Unit(
                course_id=course.id,
                title=u_data["title"],
                description=u_data["description"],
                order_index=u_data["order_index"]
            )
            session.add(unit)
            await session.flush()

            for l_data in u_data["lessons"]:
                lesson = Lesson(
                    unit_id=unit.id,
                    title=l_data["title"],
                    description=l_data["description"],
                    xp_reward=l_data["xp_reward"],
                    order_index=l_data["order_index"]
                )
                session.add(lesson)
                await session.flush()

                # Add some dummy exercises
                exercises = []
                if l_data["title"] == "Гласные":
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="multiple_choice", payload={"question": "Как читается 'ㅏ'?", "options": ["а", "о", "у", "и"], "correct": "а"}, order_index=0),
                        Exercise(lesson_id=lesson.id, type="multiple_choice", payload={"question": "Как читается 'ㅓ'?", "options": ["а", "о", "у", "и"], "correct": "о"}, order_index=1),
                    ]
                elif l_data["title"] == "Согласные":
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="multiple_choice", payload={"question": "Как читается 'ㄱ'?", "options": ["г/к", "д/т", "б/п", "с"], "correct": "г/к"}, order_index=0),
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "ㄴ", "translation": "н"}, order_index=1)
                    ]
                elif l_data["title"] == "Слоги":
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "가", "translation": "ка"}, order_index=0),
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "나", "translation": "на"}, order_index=1)
                    ]
                elif l_data["title"] == "Здравствуйте":
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "안녕하세요", "translation": "Здравствуйте"}, order_index=0),
                        Exercise(lesson_id=lesson.id, type="multiple_choice", payload={"question": "Что значит '안녕하세요'?", "options": ["До свидания", "Спасибо", "Здравствуйте", "Извините"], "correct": "Здравствуйте"}, order_index=1)
                    ]
                elif l_data["title"] == "Как дела?":
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "잘 지내요?", "translation": "Как дела?"}, order_index=0)
                    ]
                elif l_data["title"] == "Корейские числительные":
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "하나", "translation": "Один"}, order_index=0),
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "둘", "translation": "Два"}, order_index=1),
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "셋", "translation": "Три"}, order_index=2)
                    ]
                elif l_data["title"] == "Китайские числительные":
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "일", "translation": "Один"}, order_index=0),
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "이", "translation": "Два"}, order_index=1),
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "삼", "translation": "Три"}, order_index=2)
                    ]
                else:
                    exercises = [
                        Exercise(lesson_id=lesson.id, type="multiple_choice", payload={"question": "Test question 1", "options": ["A", "B", "C"], "correct": "A"}, order_index=0),
                        Exercise(lesson_id=lesson.id, type="translation", payload={"text": "Hello", "translation": "Привет"}, order_index=1)
                    ]
                
                for ex in exercises:
                    session.add(ex)

        await session.commit()
        print("Database seeded with mock Course, Units, and Lessons!")

if __name__ == "__main__":
    asyncio.run(seed_db())
