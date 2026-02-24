import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.getcwd())

from sqlalchemy import text
from app.core.db import engine

async def check_columns():
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';"))
            columns = [row[0] for row in result.fetchall()]
            print(f"Columns in users: {columns}")
            if 'is_verified' in columns:
                print("Status: Columns exist")
            else:
                print("Status: Columns missing")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_columns())
