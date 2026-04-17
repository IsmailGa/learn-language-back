import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.course import Course

class UserCourse(SQLModel, table=True):
    __tablename__ = "user_courses"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    course_id: uuid.UUID = Field(foreign_key="courses.id", index=True)
    
    xp: int = Field(default=0)
    is_active: bool = Field(default=False)
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: "User" = Relationship(back_populates="user_courses")
    course: "Course" = Relationship()
