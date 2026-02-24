import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.core.db import engine

async def update_db():
    try:
        async with engine.begin() as conn:
            print("Adding is_verified column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE NOT NULL;"))
            print("Adding verification_token column...")
            await conn.execute(text("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);"))
            print("Done.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(update_db())
