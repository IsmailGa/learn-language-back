from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import logging.config
import pathlib
import sys

from app.core.config import settings
from app.core.db import init_db
from app.api.v1.router import router as api_v1_router

LOGGING_CONFIG = pathlib.Path(__file__).parent / "../logging.conf"
logging.config.fileConfig(LOGGING_CONFIG, disable_existing_loggers=False)

logger = logging.getLogger("app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    await init_db()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Language Learning Platform API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "app": settings.APP_NAME}
