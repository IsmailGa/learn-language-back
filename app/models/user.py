import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, String, BigInteger
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.progress import UserProgress


class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    # Auth fields - support multiple auth methods
    telegram_id: Optional[int] = Field(
        default=None, 
        sa_column=Column(BigInteger, unique=True, index=True, nullable=True)
    )
    email: Optional[str] = Field(
        default=None, 
        sa_column=Column(String(255), unique=True, index=True, nullable=True)
    )
    hashed_password: Optional[str] = Field(default=None)
    
    # Verification
    is_verified: bool = Field(default=False)
    verification_token: Optional[str] = Field(default=None)
    
    # Profile
    username: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None)
    
    # Gamification
    hearts: int = Field(default=5)
    xp: int = Field(default=0)
    streak: int = Field(default=0)
    last_heart_refill_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    progress: list["UserProgress"] = Relationship(back_populates="user")