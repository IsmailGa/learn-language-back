import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, JSON
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.progress import UserProgress
    from app.models.language import Language


class Course(SQLModel, table=True):
    __tablename__ = "courses"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)
    
    source_lang_id: uuid.UUID = Field(foreign_key="languages.id", index=True)
    target_lang_id: uuid.UUID = Field(foreign_key="languages.id", index=True)
    
    is_active: bool = Field(default=True)
    
    source_lang: "Language" = Relationship(sa_relationship_kwargs={"foreign_keys": "[Course.source_lang_id]"})
    target_lang: "Language" = Relationship(sa_relationship_kwargs={"foreign_keys": "[Course.target_lang_id]"})
    
    units: list["Unit"] = Relationship(back_populates="course")
    characters: list["Character"] = Relationship(back_populates="course")


class Character(SQLModel, table=True):
    __tablename__ = "characters"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="courses.id")
    character: str = Field(max_length=50)
    transliteration: str = Field(max_length=50)
    type: str = Field(max_length=50) # e.g. "vowel", "consonant"
    audio_url: Optional[str] = Field(default=None)
    order_index: int = Field(default=0)
    
    course: Course = Relationship(back_populates="characters")


class Unit(SQLModel, table=True):
    __tablename__ = "units"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    course_id: uuid.UUID = Field(foreign_key="courses.id")
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)
    order_index: int = Field(default=0)
    
    course: Course = Relationship(back_populates="units")
    lessons: list["Lesson"] = Relationship(back_populates="unit")


class Lesson(SQLModel, table=True):
    __tablename__ = "lessons"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    unit_id: uuid.UUID = Field(foreign_key="units.id")
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None)
    xp_reward: int = Field(default=10)
    order_index: int = Field(default=0)
    
    unit: Unit = Relationship(back_populates="lessons")
    exercises: list["Exercise"] = Relationship(back_populates="lesson")
    progress: list["UserProgress"] = Relationship(back_populates="lesson")


class Exercise(SQLModel, table=True):
    __tablename__ = "exercises"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    lesson_id: uuid.UUID = Field(foreign_key="lessons.id")
    type: str = Field(max_length=50)
    payload: dict = Field(default_factory=dict, sa_column=Column(JSON))
    order_index: int = Field(default=0)
    
    lesson: Lesson = Relationship(back_populates="exercises")
