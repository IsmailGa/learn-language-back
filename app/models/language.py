import uuid
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class Language(SQLModel, table=True):
    __tablename__ = "languages"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(max_length=10, unique=True, index=True) # e.g. "en", "ru", "ko"
    name: str = Field(max_length=100) # e.g. "English", "Russian"
    native_name: str = Field(max_length=100) # e.g. "English", "Русский"
    flag_emoji: Optional[str] = Field(default=None, max_length=10)
    
    # Relationships will be added to Course model
