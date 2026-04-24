import uuid
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class Language(SQLModel, table=True):
    __tablename__ = "languages"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    code: str = Field(max_length=10, unique=True, index=True)
    name: str = Field(max_length=100)
    native_name: str = Field(max_length=100)
    flag_emoji: Optional[str] = Field(default=None, max_length=10)
    
