import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Lesson


class UserProgress(SQLModel, table=True):
    __tablename__ = "user_progress"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    lesson_id: uuid.UUID = Field(foreign_key="lessons.id", index=True)
    completed_at: datetime = Field(default_factory=datetime.utcnow)
    xp_earned: int = Field(default=0)
    mistakes: int = Field(default=0)
    
    user: "User" = Relationship(back_populates="progress")
    lesson: "Lesson" = Relationship(back_populates="progress")
