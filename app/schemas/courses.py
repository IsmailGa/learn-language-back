from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from uuid import UUID

class CourseBase(BaseModel):
    title: str
    description: Optional[str] = None
    source_lang_id: UUID
    target_lang_id: UUID
    is_active: bool = True

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    source_lang_id: Optional[UUID] = None
    target_lang_id: Optional[UUID] = None
    is_active: Optional[bool] = None

class LanguageSchema(BaseModel):
    id: UUID
    code: str
    name: str
    native_name: str
    flag_emoji: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UnitSchema(BaseModel):
    id: UUID
    course_id: UUID
    title: str
    description: Optional[str] = None
    order_index: int

    model_config = ConfigDict(from_attributes=True)

class CharacterSchema(BaseModel):
    id: UUID
    course_id: UUID
    character: str
    transliteration: str
    type: str
    audio_url: Optional[str] = None
    order_index: int

    model_config = ConfigDict(from_attributes=True)

class ExerciseSchema(BaseModel):
    id: UUID
    lesson_id: UUID
    type: str
    payload: dict
    order_index: int
    model_config = ConfigDict(from_attributes=True)

class LessonSchema(BaseModel):
    id: UUID
    unit_id: UUID
    title: str
    description: Optional[str] = None
    xp_reward: int
    order_index: int
    model_config = ConfigDict(from_attributes=True)

class UnitWithLessons(UnitSchema):
    lessons: List[LessonSchema] = []
    model_config = ConfigDict(from_attributes=True)

class LessonWithExercises(LessonSchema):
    exercises: List[ExerciseSchema] = []
    model_config = ConfigDict(from_attributes=True)

class Course(CourseBase):
    id: UUID
    source_lang: Optional[LanguageSchema] = None
    target_lang: Optional[LanguageSchema] = None
    model_config = ConfigDict(from_attributes=True)

class CourseWithUnits(Course):
    units: List[UnitSchema] = []
    model_config = ConfigDict(from_attributes=True)