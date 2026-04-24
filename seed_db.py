import asyncio
import sys
import os

sys.path.append(os.getcwd())

from sqlalchemy import select
from app.core.db import async_session_maker
from app.models.course import Course, Unit, Lesson, Exercise, Character
from app.models.language import Language

# ─────────────────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ─────────────────────────────────────────────────────────────────────────────

def mc(question: str, options: list[str], correct: str, idx: int) -> dict:
    """Создаёт упражнение типа multiple_choice."""
    return {
        "type": "multiple_choice",
        "payload": {"question": question, "options": options, "correct": correct},
        "order_index": idx,
    }

def draw(question: str, target_char: str, hint: str, idx: int) -> dict:
    """Создаёт упражнение типа draw (рисование символа)."""
    return {
        "type": "draw",
        "payload": {
            "question": question,
            "target_character": target_char,
            "hint": hint,
        },
        "order_index": idx,
    }


async def upsert_language(session, data: dict) -> Language:
    result = await session.execute(select(Language).where(Language.code == data["code"]))
    lang = result.scalar_one_or_none()
    if not lang:
        lang = Language(**data)
        session.add(lang)
        await session.flush()
        print(f"  ✓ Created lang: {data['code']}")
    else:
        for k, v in data.items():
            setattr(lang, k, v)
        session.add(lang)
    return lang


async def create_course_if_missing(session, title: str, desc: str,
                                   source_id, target_id) -> tuple[Course, bool]:
    result = await session.execute(
        select(Course).where(
            Course.title == title,
            Course.source_lang_id == source_id,
            Course.target_lang_id == target_id,
        )
    )
    course = result.scalar_one_or_none()
    if course:
        return course, False

    course = Course(title=title, description=desc,
                    source_lang_id=source_id, target_lang_id=target_id,
                    is_active=True)
    session.add(course)
    await session.flush()
    return course, True


async def create_unit(session, course_id, title: str, desc: str,
                      order_index: int, lessons_data: list) -> Unit:
    unit = Unit(course_id=course_id, title=title,
                description=desc, order_index=order_index)
    session.add(unit)
    await session.flush()

    for l_data in lessons_data:
        lesson = Lesson(
            unit_id=unit.id,
            title=l_data["title"],
            description=l_data["description"],
            xp_reward=l_data.get("xp_reward", 10),
            order_index=l_data["order_index"],
        )
        session.add(lesson)
        await session.flush()
        for e_data in l_data.get("exercises", []):
            session.add(Exercise(
                lesson_id=lesson.id,
                type=e_data["type"],
                payload=e_data["payload"],
                order_index=e_data["order_index"],
            ))
        await session.flush()
    return unit


# ─────────────────────────────────────────────────────────────────────────────
# Данные алфавита
# ─────────────────────────────────────────────────────────────────────────────

KOREAN_CHARS = [
    # Гласные
    {"char": "ㅏ", "trans": "а",   "type": "vowel"},
    {"char": "ㅑ", "trans": "я",   "type": "vowel"},
    {"char": "ㅓ", "trans": "о",   "type": "vowel"},
    {"char": "ㅕ", "trans": "ё",   "type": "vowel"},
    {"char": "ㅗ", "trans": "о",   "type": "vowel"},
    {"char": "ㅛ", "trans": "ё",   "type": "vowel"},
    {"char": "ㅜ", "trans": "у",   "type": "vowel"},
    {"char": "ㅠ", "trans": "ю",   "type": "vowel"},
    {"char": "ㅡ", "trans": "ы",   "type": "vowel"},
    {"char": "ㅣ", "trans": "и",   "type": "vowel"},
    {"char": "ㅐ", "trans": "э",   "type": "vowel"},
    {"char": "ㅔ", "trans": "е",   "type": "vowel"},
    # Согласные
    {"char": "ㄱ", "trans": "г/к", "type": "consonant"},
    {"char": "ㄴ", "trans": "н",   "type": "consonant"},
    {"char": "ㄷ", "trans": "д/т", "type": "consonant"},
    {"char": "ㄹ", "trans": "р/ль","type": "consonant"},
    {"char": "ㅁ", "trans": "м",   "type": "consonant"},
    {"char": "ㅂ", "trans": "б/п", "type": "consonant"},
    {"char": "ㅅ", "trans": "с",   "type": "consonant"},
    {"char": "ㅇ", "trans": "нг",  "type": "consonant"},
    {"char": "ㅈ", "trans": "дж",  "type": "consonant"},
    {"char": "ㅊ", "trans": "чх",  "type": "consonant"},
    {"char": "ㅋ", "trans": "кх",  "type": "consonant"},
    {"char": "ㅌ", "trans": "тх",  "type": "consonant"},
    {"char": "ㅍ", "trans": "пх",  "type": "consonant"},
    {"char": "ㅎ", "trans": "х",   "type": "consonant"},
]

ENGLISH_CHARS = [
    {"char": c, "trans": c.lower(),
     "type": "vowel" if c.lower() in "aeiou" else "consonant"}
    for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
]


# ─────────────────────────────────────────────────────────────────────────────
# Курс: Корейский (RU → KO)
# ─────────────────────────────────────────────────────────────────────────────

KOREAN_RU_UNITS = [
    {
        "title": "Хангыль",
        "description": "Алфавит и чтение",
        "order_index": 0,
        "lessons": [
            {
                "title": "Гласные буквы",
                "description": "Базовые гласные звуки хангыля",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("Как произносится ㅏ?",    ["а","о","у","и"],       "а",  0),
                    mc("Выберите символ для 'и'",  ["ㅏ","ㅣ","ㅡ","ㅗ"],   "ㅣ", 1),
                    mc("Как произносится ㅗ?",    ["о","а","у","э"],       "о",  2),
                    mc("Выберите символ для 'у'",  ["ㅏ","ㅣ","ㅜ","ㅗ"],   "ㅜ", 3),
                    mc("Как произносится ㅡ?",    ["ы","е","и","о"],       "ы",  4),
                ],
            },
            {
                "title": "Согласные буквы",
                "description": "Базовые согласные хангыля",
                "xp_reward": 10, "order_index": 1,
                "exercises": [
                    mc("Как произносится ㄴ?",    ["м","н","р","к"],       "н",  0),
                    mc("Выберите символ для 'м'",  ["ㄴ","ㅁ","ㄹ","ㅂ"],   "ㅁ", 1),
                    mc("Как произносится ㄱ?",    ["г/к","н","р","х"],     "г/к",2),
                    mc("Символ звука 'с':",        ["ㄱ","ㄴ","ㅅ","ㅎ"],   "ㅅ", 3),
                    mc("Как произносится ㅎ?",    ["п","м","х","к"],       "х",  4),
                ],
            },
            {
                "title": "Слоги: первые шаги",
                "description": "Составление слогов из гласных и согласных",
                "xp_reward": 15, "order_index": 2,
                "exercises": [
                    mc("Как читается 가?",         ["ка","на","ма","са"],   "ка", 0),
                    mc("Как читается 나?",         ["га","на","да","ра"],   "на", 1),
                    mc("Как читается 마?",         ["ка","на","ма","ха"],   "ма", 2),
                    mc("Как читается 바?",         ["ба","на","ма","да"],   "ба", 3),
                ],
            },
            {
                "title": "Нарисуй: гласные",
                "description": "Практика рисования гласных хангыля",
                "xp_reward": 20, "order_index": 3,
                "exercises": [
                    draw("Нарисуйте ㅏ на холсте", "ㅏ", "Вертикальная черта + короткая вправо", 0),
                    draw("Нарисуйте ㅣ на холсте", "ㅣ", "Просто вертикальная черта", 1),
                    draw("Нарисуйте ㅗ на холсте", "ㅗ", "Горизонтальная черта сверху + вертикальная вниз", 2),
                ],
            },
        ],
    },
    {
        "title": "Приветствия",
        "description": "Знакомство и базовые фразы",
        "order_index": 1,
        "lessons": [
            {
                "title": "Здравствуйте",
                "description": "Формальные приветствия",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("Как сказать 'Здравствуйте'?",
                       ["안녕하세요","감사합니다","죄송합니다","안녕"], "안녕하세요", 0),
                    mc("'Привет' (неформально):",
                       ["안녕","감사합니다","죄송합니다","네"], "안녕", 1),
                    mc("'До свидания' (формально):",
                       ["안녕히 가세요","괜찮아요","감사합니다","미안해요"], "안녕히 가세요", 2),
                    mc("'Меня зовут...' → 제 이름은... означает:",
                       ["Меня зовут","Я люблю","Я хочу","Мне нравится"], "Меня зовут", 3),
                ],
            },
            {
                "title": "Благодарности",
                "description": "Как сказать спасибо и извините",
                "xp_reward": 10, "order_index": 1,
                "exercises": [
                    mc("Как сказать 'Спасибо'?",
                       ["미안해요","괜찮아요","감사합니다","아니요"], "감사합니다", 0),
                    mc("'Извините' (официально):",
                       ["감사합니다","죄송합니다","괜찮아요","네"], "죄송합니다", 1),
                    mc("'Пожалуйста / Ничего страшного':",
                       ["미안해요","괜찮아요","감사합니다","아니요"], "괜찮아요", 2),
                ],
            },
            {
                "title": "Да, Нет, Ладно",
                "description": "Базовые ответные слова",
                "xp_reward": 10, "order_index": 2,
                "exercises": [
                    mc("네 означает:", ["Да","Нет","Может","Не знаю"], "Да", 0),
                    mc("아니요 означает:", ["Да","Нет","Спасибо","Привет"], "Нет", 1),
                    mc("알겠어요 означает:", ["Понял/Ладно","Извините","Спасибо","Привет"], "Понял/Ладно", 2),
                    mc("모르겠어요 означает:", ["Понял","Не знаю","Спасибо","Привет"], "Не знаю", 3),
                ],
            },
        ],
    },
    {
        "title": "Числа",
        "description": "Корейские и китайские числа",
        "order_index": 2,
        "lessons": [
            {
                "title": "Числа 1–10 (китайские)",
                "description": "Система чисел для цен, этажей, месяцев",
                "xp_reward": 15, "order_index": 0,
                "exercises": [
                    mc("일 — это:", ["1","2","3","4"], "1", 0),
                    mc("이 — это:", ["1","2","3","4"], "2", 1),
                    mc("삼 — это:", ["3","4","5","6"], "3", 2),
                    mc("사 — это:", ["7","4","5","6"], "4", 3),
                    mc("오 — это:", ["3","4","5","6"], "5", 4),
                    mc("육 — это:", ["5","6","7","8"], "6", 5),
                    mc("칠 — это:", ["6","7","8","9"], "7", 6),
                    mc("팔 — это:", ["7","8","9","10"],"8", 7),
                    mc("구 — это:", ["8","9","10","11"],"9", 8),
                    mc("십 — это:", ["9","10","11","12"],"10",9),
                ],
            },
            {
                "title": "Числа 1–10 (корейские)",
                "description": "Нативная система для штук, возраста, часов",
                "xp_reward": 15, "order_index": 1,
                "exercises": [
                    mc("하나 — это:", ["1","2","3","4"], "1", 0),
                    mc("둘 — это:",   ["1","2","3","4"], "2", 1),
                    mc("셋 — это:",   ["3","4","5","6"], "3", 2),
                    mc("넷 — это:",   ["3","4","5","6"], "4", 3),
                    mc("다섯 — это:", ["4","5","6","7"], "5", 4),
                    mc("여섯 — это:", ["5","6","7","8"], "6", 5),
                    mc("일곱 — это:", ["6","7","8","9"], "7", 6),
                    mc("여덟 — это:", ["7","8","9","10"],"8", 7),
                    mc("아홉 — это:", ["8","9","10","11"],"9", 8),
                    mc("열 — это:",   ["9","10","11","12"],"10",9),
                ],
            },
        ],
    },
    {
        "title": "Цвета и вещи",
        "description": "Базовая лексика повседневной жизни",
        "order_index": 3,
        "lessons": [
            {
                "title": "Цвета",
                "description": "Основные цвета на корейском",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("빨간색 означает:", ["Красный","Синий","Зелёный","Жёлтый"], "Красный", 0),
                    mc("파란색 означает:", ["Красный","Синий","Зелёный","Жёлтый"], "Синий", 1),
                    mc("노란색 означает:", ["Красный","Белый","Зелёный","Жёлтый"], "Жёлтый", 2),
                    mc("초록색 означает:", ["Оранжевый","Синий","Зелёный","Фиолетовый"], "Зелёный", 3),
                    mc("하얀색 означает:", ["Чёрный","Белый","Серый","Синий"], "Белый", 4),
                    mc("검은색 означает:", ["Чёрный","Белый","Серый","Синий"], "Чёрный", 5),
                ],
            },
            {
                "title": "Вещи вокруг нас",
                "description": "Названия предметов",
                "xp_reward": 10, "order_index": 1,
                "exercises": [
                    mc("책 означает:", ["Книга","Ручка","Стол","Стул"], "Книга", 0),
                    mc("의자 означает:", ["Книга","Ручка","Стол","Стул"], "Стул", 1),
                    mc("물 означает:", ["Еда","Вода","Сок","Чай"], "Вода", 2),
                    mc("밥 означает:", ["Еда/Рис","Вода","Сок","Чай"], "Еда/Рис", 3),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Курс: Английский (RU → EN)
# ─────────────────────────────────────────────────────────────────────────────

ENGLISH_RU_UNITS = [
    {
        "title": "Алфавит",
        "description": "Английские буквы и произношение",
        "order_index": 0,
        "lessons": [
            {
                "title": "Буквы A–F",
                "description": "Первые шесть букв алфавита",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("Как произносится A?", ["эй"," би","си","ди"], "эй", 0),
                    mc("Как произносится B?", ["эй"," би","си","ди"], "би", 1),
                    mc("Как произносится C?", ["эй","би","си","ди"], "си", 2),
                    mc("Как произносится D?", ["эй","ди","эф","джи"], "ди", 3),
                    mc("Как произносится E?", ["и","ди","эф","джи"], "и", 4),
                    mc("Как произносится F?", ["и","эф","джи","эйч"], "эф", 5),
                ],
            },
            {
                "title": "Нарисуй: буквы A–E",
                "description": "Практика написания первых букв",
                "xp_reward": 20, "order_index": 1,
                "exercises": [
                    draw("Нарисуйте букву A", "A", "Две наклонные линии + перекладина", 0),
                    draw("Нарисуйте букву B", "B", "Вертикальная + два полукруга вправо", 1),
                    draw("Нарисуйте букву C", "C", "Незамкнутая дуга влево", 2),
                ],
            },
        ],
    },
    {
        "title": "Приветствия",
        "description": "Hello, Goodbye и базовые фразы",
        "order_index": 1,
        "lessons": [
            {
                "title": "Привет и пока",
                "description": "Первые фразы на английском",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("Как сказать 'Привет'?", ["Hello","Bye","Thanks","Yes"], "Hello", 0),
                    mc("Как сказать 'До свидания'?", ["Please","Bye","Sorry","No"], "Bye", 1),
                    mc("Как сказать 'Доброе утро'?", ["Good morning","Good night","Good luck","Thank you"], "Good morning", 2),
                    mc("Как сказать 'Добрый вечер'?", ["Good morning","Good evening","Goodbye","Sorry"], "Good evening", 3),
                ],
            },
            {
                "title": "Благодарности и вежливость",
                "description": "Please, Thank you, Sorry",
                "xp_reward": 10, "order_index": 1,
                "exercises": [
                    mc("Как сказать 'Спасибо'?",         ["Hello","Thanks","Sorry","Yes"],   "Thanks", 0),
                    mc("Как сказать 'Пожалуйста'?",      ["Please","Sorry","No","Yes"],       "Please", 1),
                    mc("Как сказать 'Извините'?",         ["Please","Thank you","Sorry","Yes"],"Sorry", 2),
                    mc("Как сказать 'Не за что'?",        ["You're welcome","Sorry","Please","Thanks"],"You're welcome",3),
                ],
            },
        ],
    },
    {
        "title": "Числа и счёт",
        "description": "Числа 1–20 на английском",
        "order_index": 2,
        "lessons": [
            {
                "title": "Числа 1–10",
                "description": "One, Two, Three...",
                "xp_reward": 15, "order_index": 0,
                "exercises": [
                    mc("One — это:", ["1","2","3","4"], "1", 0),
                    mc("Two — это:", ["1","2","3","4"], "2", 1),
                    mc("Three — это:", ["3","4","5","6"], "3", 2),
                    mc("Four — это:", ["3","4","5","6"], "4", 3),
                    mc("Five — это:", ["4","5","6","7"], "5", 4),
                    mc("Six — это:", ["5","6","7","8"], "6", 5),
                    mc("Seven — это:", ["6","7","8","9"], "7", 6),
                    mc("Eight — это:", ["7","8","9","10"],"8", 7),
                    mc("Nine — это:", ["8","9","10","11"],"9", 8),
                    mc("Ten — это:", ["9","10","11","12"],"10",9),
                ],
            },
        ],
    },
    {
        "title": "Цвета и вещи",
        "description": "Базовая лексика по-английски",
        "order_index": 3,
        "lessons": [
            {
                "title": "Цвета",
                "description": "Red, Blue, Green...",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("Red означает:", ["Красный","Синий","Зелёный","Жёлтый"], "Красный", 0),
                    mc("Blue означает:", ["Красный","Синий","Зелёный","Жёлтый"], "Синий", 1),
                    mc("Green означает:", ["Красный","Синий","Зелёный","Жёлтый"], "Зелёный", 2),
                    mc("Yellow означает:", ["Красный","Жёлтый","Зелёный","Фиолетовый"], "Жёлтый", 3),
                    mc("White означает:", ["Чёрный","Белый","Серый","Синий"], "Белый", 4),
                    mc("Black означает:", ["Чёрный","Белый","Серый","Синий"], "Чёрный", 5),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# Курс: Корейский (EN → KO) — для носителей английского
# ─────────────────────────────────────────────────────────────────────────────

KOREAN_EN_UNITS = [
    {
        "title": "Hangul",
        "description": "The Korean alphabet",
        "order_index": 0,
        "lessons": [
            {
                "title": "Vowels",
                "description": "Basic Korean vowel sounds",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("ㅏ sounds like:", ["a","o","u","i"],  "a",  0),
                    mc("ㅣ sounds like:", ["a","e","i","o"],  "i",  1),
                    mc("ㅗ sounds like:", ["a","i","u","o"],  "o",  2),
                    mc("ㅜ sounds like:", ["a","e","u","o"],  "u",  3),
                    mc("ㅡ is closest to:", ["a","eu","i","o"],"eu", 4),
                ],
            },
            {
                "title": "Consonants",
                "description": "Basic Korean consonant sounds",
                "xp_reward": 10, "order_index": 1,
                "exercises": [
                    mc("ㄴ sounds like:", ["m","n","r","k"],  "n",  0),
                    mc("ㅁ sounds like:", ["m","n","r","k"],  "m",  1),
                    mc("ㄱ sounds like:", ["g/k","n","r","h"],"g/k",2),
                    mc("ㅎ sounds like:", ["p","m","h","k"],  "h",  3),
                    mc("ㄹ sounds like:", ["m","n","r/l","k"],"r/l",4),
                ],
            },
            {
                "title": "Draw: Vowels",
                "description": "Practice drawing Korean vowels",
                "xp_reward": 20, "order_index": 2,
                "exercises": [
                    draw("Draw ㅏ on the canvas", "ㅏ", "Vertical line + short horizontal to the right", 0),
                    draw("Draw ㅣ on the canvas", "ㅣ", "A simple vertical line", 1),
                    draw("Draw ㅗ on the canvas", "ㅗ", "Horizontal line on top with a vertical going down", 2),
                ],
            },
        ],
    },
    {
        "title": "Greetings",
        "description": "Hello and basic Korean phrases",
        "order_index": 1,
        "lessons": [
            {
                "title": "Hello & Goodbye",
                "description": "Essential Korean greetings",
                "xp_reward": 10, "order_index": 0,
                "exercises": [
                    mc("'Hello' in Korean:", ["안녕하세요","감사합니다","죄송합니다","안녕"], "안녕하세요", 0),
                    mc("Informal 'Hi':", ["안녕","감사합니다","죄송합니다","네"], "안녕", 1),
                    mc("'Thank you' in Korean:", ["미안해요","괜찮아요","감사합니다","아니요"], "감사합니다", 2),
                    mc("'Yes' in Korean:", ["아니요","네","감사합니다","안녕"], "네", 3),
                    mc("'No' in Korean:", ["아니요","네","감사합니다","안녕"], "아니요", 4),
                ],
            },
        ],
    },
    {
        "title": "Numbers",
        "description": "Korean numbers and counting",
        "order_index": 2,
        "lessons": [
            {
                "title": "Numbers 1–5 (Sino-Korean)",
                "description": "일, 이, 삼, 사, 오",
                "xp_reward": 15, "order_index": 0,
                "exercises": [
                    mc("일 means:", ["1","2","3","4"], "1", 0),
                    mc("이 means:", ["1","2","3","4"], "2", 1),
                    mc("삼 means:", ["3","4","5","6"], "3", 2),
                    mc("사 means:", ["7","4","5","6"], "4", 3),
                    mc("오 means:", ["3","4","5","6"], "5", 4),
                ],
            },
        ],
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Главная функция
# ─────────────────────────────────────────────────────────────────────────────

async def seed_db():
    print("\n🌱 Starting database seeding...\n")
    async with async_session_maker() as session:

        # 1. Языки
        print("── Languages ──────────────────────────────")
        langs_data = [
            {"code": "ru", "name": "Russian",  "native_name": "Русский",   "flag_emoji": "🇷🇺"},
            {"code": "ko", "name": "Korean",   "native_name": "한국어",     "flag_emoji": "🇰🇷"},
            {"code": "en", "name": "English",  "native_name": "English",   "flag_emoji": "🇺🇸"},
            {"code": "uz", "name": "Uzbek",    "native_name": "O'zbek",    "flag_emoji": "🇺🇿"},
        ]
        lang_map: dict[str, object] = {}
        for l_data in langs_data:
            lang = await upsert_language(session, l_data)
            lang_map[l_data["code"]] = lang.id

        # ── 2. Korean Course (RU → KO) ────────────────────────────────────
        print("\n── Korean Course (RU → KO) ────────────────")
        ko_ru, created = await create_course_if_missing(
            session, "Корейский", "Базовый курс корейского языка (A1–A2)",
            lang_map["ru"], lang_map["ko"]
        )
        if created:
            for idx, c_data in enumerate(KOREAN_CHARS):
                session.add(Character(
                    course_id=ko_ru.id, character=c_data["char"],
                    transliteration=c_data["trans"], type=c_data["type"],
                    order_index=idx
                ))
            await session.flush()
            for u_data in KOREAN_RU_UNITS:
                await create_unit(session, ko_ru.id,
                                  u_data["title"], u_data["description"],
                                  u_data["order_index"], u_data["lessons"])
            print(f"  ✓ Created Korean (RU) course with {len(KOREAN_RU_UNITS)} units")
        else:
            print("  ⏭  Korean (RU) course already exists")

        # ── 3. English Course (RU → EN) ────────────────────────────────────
        print("\n── English Course (RU → EN) ───────────────")
        en_ru, created = await create_course_if_missing(
            session, "Английский", "Базовый курс английского языка (A1–A2)",
            lang_map["ru"], lang_map["en"]
        )
        if created:
            for idx, c_data in enumerate(ENGLISH_CHARS):
                session.add(Character(
                    course_id=en_ru.id, character=c_data["char"],
                    transliteration=c_data["trans"], type=c_data["type"],
                    order_index=idx
                ))
            await session.flush()
            for u_data in ENGLISH_RU_UNITS:
                await create_unit(session, en_ru.id,
                                  u_data["title"], u_data["description"],
                                  u_data["order_index"], u_data["lessons"])
            print(f"  ✓ Created English (RU) course with {len(ENGLISH_RU_UNITS)} units")
        else:
            print("  ⏭  English (RU) course already exists")

        # ── 4. Korean Course (EN → KO) ────────────────────────────────────
        print("\n── Korean Course (EN → KO) ────────────────")
        ko_en, created = await create_course_if_missing(
            session, "Korean", "Basic Korean language course (A1–A2)",
            lang_map["en"], lang_map["ko"]
        )
        if created:
            for idx, c_data in enumerate(KOREAN_CHARS):
                session.add(Character(
                    course_id=ko_en.id, character=c_data["char"],
                    transliteration=c_data["trans"], type=c_data["type"],
                    order_index=idx
                ))
            await session.flush()
            for u_data in KOREAN_EN_UNITS:
                await create_unit(session, ko_en.id,
                                  u_data["title"], u_data["description"],
                                  u_data["order_index"], u_data["lessons"])
            print(f"  ✓ Created Korean (EN) course with {len(KOREAN_EN_UNITS)} units")
        else:
            print("  ⏭  Korean (EN) course already exists")

        await session.commit()
        print("\n✅ Database seeded successfully!\n")


if __name__ == "__main__":
    asyncio.run(seed_db())
