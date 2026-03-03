import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.getcwd())

from sqlalchemy import select
from app.core.db import async_session_maker
from app.models.course import Course, Unit, Lesson, Exercise, Character
from app.models.language import Language
from app.models.user_course import UserCourse

async def seed_db():
    print("Starting database seeding...")
    async with async_session_maker() as session:
        # 1. Add Languages
        print("Adding/Checking languages...")
        languages_data = [
            {"code": "ru", "name": "Russian", "native_name": "Русский", "flag_emoji": "🇷🇺"},
            {"code": "ko", "name": "Korean", "native_name": "한국어", "flag_emoji": "🇰🇷"},
            {"code": "en", "name": "English", "native_name": "English", "flag_emoji": "🇺🇸"},
            {"code": "uz", "name": "Uzbek", "native_name": "O'zbek", "flag_emoji": "🇺🇿"},
        ]
        
        lang_map = {}
        for l_data in languages_data:
            result = await session.execute(select(Language).where(Language.code == l_data["code"]))
            lang = result.scalar_one_or_none()
            if not lang:
                lang = Language(**l_data)
                session.add(lang)
                await session.flush()
                print(f"Created language: {l_data['code']}")
            else:
                for key, value in l_data.items():
                    setattr(lang, key, value)
                session.add(lang)
                print(f"Verified language: {l_data['code']}")
            lang_map[l_data["code"]] = lang.id

        # 2. Add Korean Course (Target: KO, Source: RU)
        print("Checking Korean course...")
        result = await session.execute(
            select(Course).where(
                Course.title == "Корейский",
                Course.source_lang_id == lang_map["ru"],
                Course.target_lang_id == lang_map["ko"]
            )
        )
        course = result.scalar_one_or_none()
        
        if not course:
            print("Creating Korean course and its content...")
            course = Course(
                title="Корейский",
                description="Базовый курс корейского языка",
                source_lang_id=lang_map["ru"],
                target_lang_id=lang_map["ko"],
                is_active=True
            )
            session.add(course)
            await session.flush()

            # Create Characters
            characters_data = [
                {"char": "ㅏ", "trans": "а", "type": "vowel"},
                {"char": "ㅑ", "trans": "я", "type": "vowel"},
                {"char": "ㅓ", "trans": "о", "type": "vowel"},
                {"char": "ㅕ", "trans": "ё", "type": "vowel"},
                {"char": "ㅗ", "trans": "о", "type": "vowel"},
                {"char": "ㅛ", "trans": "ё", "type": "vowel"},
                {"char": "ㅜ", "trans": "у", "type": "vowel"},
                {"char": "ㅠ", "trans": "ю", "type": "vowel"},
                {"char": "ㅡ", "trans": "ы", "type": "vowel"},
                {"char": "ㅣ", "trans": "и", "type": "vowel"},
                {"char": "ㅐ", "trans": "э", "type": "vowel"},
                {"char": "ㅒ", "trans": "йэ", "type": "vowel"},
                {"char": "ㅔ", "trans": "е", "type": "vowel"},
                {"char": "ㅖ", "trans": "йе", "type": "vowel"},
                {"char": "ㅘ", "trans": "ва", "type": "vowel"},
                {"char": "ㅙ", "trans": "вэ", "type": "vowel"},
                {"char": "ㅚ", "trans": "вэ", "type": "vowel"},
                {"char": "ㅝ", "trans": "во", "type": "vowel"},
                {"char": "ㅞ", "trans": "ве", "type": "vowel"},
                {"char": "ㅟ", "trans": "ви", "type": "vowel"},
                {"char": "ㅢ", "trans": "ый", "type": "vowel"},
                {"char": "ㄱ", "trans": "г/к", "type": "consonant"},
                {"char": "ㄴ", "trans": "н", "type": "consonant"},
                {"char": "ㄷ", "trans": "д/т", "type": "consonant"},
                {"char": "ㄹ", "trans": "р/ль", "type": "consonant"},
                {"char": "ㅁ", "trans": "м", "type": "consonant"},
                {"char": "ㅂ", "trans": "б/п", "type": "consonant"},
                {"char": "ㅅ", "trans": "с", "type": "consonant"},
                {"char": "ㅇ", "trans": "н (нг)", "type": "consonant"},
                {"char": "ㅈ", "trans": "дж", "type": "consonant"},
                {"char": "ㅊ", "trans": "чх", "type": "consonant"},
                {"char": "ㅋ", "trans": "кх", "type": "consonant"},
                {"char": "ㅌ", "trans": "тх", "type": "consonant"},
                {"char": "ㅍ", "trans": "пх", "type": "consonant"},
                {"char": "ㅎ", "trans": "х", "type": "consonant"},
            ]
            for idx, c_data in enumerate(characters_data):
                char = Character(
                    course_id=course.id,
                    character=c_data["char"],
                    transliteration=c_data["trans"],
                    type=c_data["type"],
                    order_index=idx
                )
                session.add(char)
            await session.flush()

            # Create Units
            units_data = [
                {
                    "title": "Хангыль",
                    "description": "Алфавит и чтение",
                    "order_index": 0,
                    "lessons": [
                        {
                            "title": "Гласные", "description": "Базовые гласные звуки", "xp_reward": 10, "order_index": 0,
                            "exercises": [
                                {"type": "multiple_choice", "payload": {"question": "Как произносится ㅏ?", "options": ["а", "о", "у", "и"], "correct": "а"}, "order_index": 0},
                                {"type": "multiple_choice", "payload": {"question": "Выберите символ для звука 'и'", "options": ["ㅏ", "ㅣ", "ㅡ", "ㅗ"], "correct": "ㅣ"}, "order_index": 1},
                                {"type": "multiple_choice", "payload": {"question": "Как произносится ㅗ?", "options": ["о", "а", "у", "э"], "correct": "о"}, "order_index": 2},
                                {"type": "multiple_choice", "payload": {"question": "Выберите символ для звука 'у'", "options": ["ㅏ", "ㅣ", "ㅜ", "ㅗ"], "correct": "ㅜ"}, "order_index": 3}
                            ]
                        },
                        {
                            "title": "Согласные", "description": "Базовые согласные звуки", "xp_reward": 10, "order_index": 1,
                            "exercises": [
                                {"type": "multiple_choice", "payload": {"question": "Как произносится ㄴ?", "options": ["м", "н", "р", "к"], "correct": "н"}, "order_index": 0},
                                {"type": "multiple_choice", "payload": {"question": "Выберите символ для звука 'м'", "options": ["ㄴ", "ㅁ", "ㄹ", "ㅂ"], "correct": "ㅁ"}, "order_index": 1}
                            ]
                        },
                        {
                            "title": "Слоги", "description": "Составление слогов", "xp_reward": 15, "order_index": 2,
                            "exercises": [
                                {"type": "multiple_choice", "payload": {"question": "Как читается 가?", "options": ["ка", "на", "ма", "са"], "correct": "ка"}, "order_index": 0}
                            ]
                        }
                    ]
                },
                {
                    "title": "Приветствия",
                    "description": "Знакомство и базовые фразы",
                    "order_index": 1,
                    "lessons": [
                        {
                            "title": "Здравствуйте", "description": "Формальные приветствия", "xp_reward": 10, "order_index": 0,
                            "exercises": [
                                {"type": "multiple_choice", "payload": {"question": "Как сказать 'Здравствуйте'?", "options": ["안녕하세요", "감사합니다", "죄송합니다", "안녕"], "correct": "안녕하세요"}, "order_index": 0},
                                {"type": "multiple_choice", "payload": {"question": "Как сказать 'Привет' (неформально)?", "options": ["안녕", "감사합니다", "죄송합니다", "네"], "correct": "안녕"}, "order_index": 1}
                            ]
                        },
                        {
                            "title": "Как дела?", "description": "Повседневные выражения", "xp_reward": 10, "order_index": 1,
                            "exercises": [
                                {"type": "multiple_choice", "payload": {"question": "Как сказать 'Спасибо'?", "options": ["미안해요", "괜찮아요", "감사합니다", "아니요"], "correct": "감사합니다"}, "order_index": 0}
                            ]
                        }
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
                    
                    if "exercises" in l_data:
                        for e_data in l_data["exercises"]:
                            exercise = Exercise(
                                lesson_id=lesson.id,
                                type=e_data["type"],
                                payload=e_data["payload"],
                                order_index=e_data["order_index"]
                            )
                            session.add(exercise)
                        await session.flush()
        else:
            print("Korean course already exists.")

        # 3. Add English Course
        print("Checking English course...")
        result = await session.execute(
            select(Course).where(
                Course.title == "Английский",
                Course.source_lang_id == lang_map["ru"],
                Course.target_lang_id == lang_map["en"]
            )
        )
        en_course = result.scalar_one_or_none()
        
        if not en_course:
            print("Creating English course...")
            en_course = Course(
                title="Английский",
                description="Базовый курс английского языка",
                source_lang_id=lang_map["ru"],
                target_lang_id=lang_map["en"],
                is_active=True
            )
            session.add(en_course)
            await session.flush()
            
            # Add English Alphabet
            print("Adding English alphabet...")
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            for idx, char in enumerate(alphabet):
                c = Character(
                    course_id=en_course.id,
                    character=char,
                    transliteration=char.lower(),
                    type="vowel" if char.lower() in "aeiou" else "consonant",
                    order_index=idx
                )
                session.add(c)
            await session.flush()
            
            en_unit = Unit(
                course_id=en_course.id,
                title="Basics",
                description="Basic English phrases",
                order_index=0
            )
            session.add(en_unit)
            await session.flush()
            
            en_lesson = Lesson(
                unit_id=en_unit.id,
                title="Greetings",
                description="Hello and Goodbye",
                xp_reward=10,
                order_index=0
            )
            session.add(en_lesson)
            await session.flush()
            
            # Adding multiple exercises for English Greetings
            en_exercises_data = [
                {"type": "multiple_choice", "payload": {"question": "Как сказать 'Привет'?", "options": ["Hello", "Bye", "Thanks", "Yes"], "correct": "Hello"}, "order_index": 0},
                {"type": "multiple_choice", "payload": {"question": "Как сказать 'До свидания'?", "options": ["Please", "Bye", "Sorry", "No"], "correct": "Bye"}, "order_index": 1},
                {"type": "multiple_choice", "payload": {"question": "Как сказать 'Спасибо'?", "options": ["Hello", "Thanks", "Sorry", "Yes"], "correct": "Thanks"}, "order_index": 2}
            ]
            
            for e_data in en_exercises_data:
                en_exercise = Exercise(
                    lesson_id=en_lesson.id,
                    type=e_data["type"],
                    payload=e_data["payload"],
                    order_index=e_data["order_index"]
                )
                session.add(en_exercise)
            await session.flush()
        else:
            print("English course already exists.")

        await session.commit()
        print("Success! Database seeded.")

if __name__ == "__main__":
    asyncio.run(seed_db())
