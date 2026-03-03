import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.core.db import engine

async def column_exists(conn, table_name, column_name):
    query = text(
        "SELECT EXISTS ("
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_name=:table AND column_name=:column"
        ");"
    )
    result = await conn.execute(query, {"table": table_name, "column": column_name})
    return result.scalar()

async def update_db():
    try:
        async with engine.connect() as conn:
            # We use separate transactions or just simple execution outside a single big 'begin' 
            # to avoid 'transaction aborted' issues if one check fails (though column_exists shouldn't fail)
            
            print("Checking is_verified column...")
            if not await column_exists(conn, "users", "is_verified"):
                await conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE NOT NULL;"))
                await conn.commit()
                print("Added is_verified column.")
            else:
                print("is_verified column already exists.")

            print("Checking verification_token column...")
            if not await column_exists(conn, "users", "verification_token"):
                await conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);"))
                await conn.commit()
                print("Added verification_token column.")
            else:
                print("verification_token column already exists.")

            print("Checking current_course_id column...")
            if not await column_exists(conn, "users", "current_course_id"):
                await conn.execute(text("ALTER TABLE users ADD COLUMN current_course_id UUID REFERENCES courses(id);"))
                await conn.commit()
                print("Added current_course_id column.")
            else:
                print("current_course_id column already exists.")
            
            print("Done.")
    except Exception as e:
        print(f"General Error: {e}")

if __name__ == "__main__":
    asyncio.run(update_db())
