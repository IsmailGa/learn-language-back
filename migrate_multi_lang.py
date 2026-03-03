import asyncio
import uuid
import sys
import os

# Add server directory to path
sys.path.append(os.getcwd())

from sqlmodel import select, Session, SQLModel
from app.core.db import engine
from app.models.language import Language
from app.models.course import Course
from sqlalchemy import text

async def migrate():
    # 1. Create tables if they don't exist (Language, UserCourse)
    async with engine.begin() as conn:
        # We need to be careful here because Course table might still have old columns
        # if we haven't run a real migration tool like Alembic.
        # For simplicity, we'll try to add the new columns first.
        try:
            await conn.execute(text("ALTER TABLE courses ADD COLUMN source_lang_id UUID REFERENCES languages(id)"))
            await conn.execute(text("ALTER TABLE courses ADD COLUMN target_lang_id UUID REFERENCES languages(id)"))
        except Exception as e:
            print(f"Columns might already exist or table doesn't exist: {e}")
        
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine) as session:
        # 2. Add default languages
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
            lang_map[l_data["code"]] = lang.id
        
        # 3. Migrate existing courses (from temp columns or if they still have source_lang/target_lang)
        # Note: If SQLModel already changed the class, accessing .source_lang might fail
        # We use raw sql if needed.
        result = await session.execute(text("SELECT id, source_lang, target_lang FROM courses"))
        courses = result.all()
        
        for c_id, s_lang, t_lang in courses:
            s_id = lang_map.get(s_lang)
            t_id = lang_map.get(t_lang)
            if s_id and t_id:
                await session.execute(
                    text("UPDATE courses SET source_lang_id = :s_id, target_lang_id = :t_id WHERE id = :c_id"),
                    {"s_id": s_id, "t_id": t_id, "c_id": c_id}
                )
        
        await session.commit()
    print("Migration completed!")

from sqlalchemy.ext.asyncio import AsyncSession
if __name__ == "__main__":
    asyncio.run(migrate())
