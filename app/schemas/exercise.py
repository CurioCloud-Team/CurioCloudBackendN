"""
练习题相关的Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.exercise import QuestionType, DifficultyLevel

class ChoiceBase(BaseModel):
    content: str
    is_correct: bool

class ChoiceCreate(ChoiceBase):
    pass

class Choice(ChoiceBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    lesson_plan_id: int
    question_type: QuestionType
    difficulty: DifficultyLevel
    content: str
    answer: Optional[str] = None

class QuestionCreate(QuestionBase):
    choices: Optional[List[ChoiceCreate]] = None

class Question(QuestionBase):
    id: int
    choices: List[Choice] = []

    class Config:
        from_attributes = True
