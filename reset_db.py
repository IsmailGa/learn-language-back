import asyncio
import sys
import os

# Add server directory to path
sys.path.append(os.getcwd())

from sqlmodel import SQLModel
from app.core.db import engine
from app.models import * # Ensure all models are loaded

async def reset_db():
    print("Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
        print("Creating all tables...")
        await conn.run_sync(SQLModel.metadata.create_all)
    print("Database reset successfully!")

if __name__ == "__main__":
    asyncio.run(reset_db())
