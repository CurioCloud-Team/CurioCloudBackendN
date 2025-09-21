"""
练习题相关的Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from app.models.exercise import QuestionType, DifficultyLevel

class ChoiceBase(BaseModel):
    """选项的基础模型"""
    content: str = Field(..., description="选项内容")
    is_correct: bool = Field(..., description="是否为正确答案")

class ChoiceCreate(ChoiceBase):
    """用于创建新选项的模型"""
    pass

class Choice(ChoiceBase):
    """用于API响应的选项模型"""
    id: int = Field(..., description="选项ID")
    question_id: int = Field(..., description="所属问题ID")

    class Config:
        from_attributes = True

class QuestionBase(BaseModel):
    """题目的基础模型"""
    lesson_plan_id: int = Field(..., description="所属教案ID")
    question_type: QuestionType = Field(..., description="题目类型")
    difficulty: DifficultyLevel = Field(..., description="题目难度")
    content: str = Field(..., description="题干内容")
    answer: Optional[str] = Field(None, description="答案或答案解析")

class QuestionCreate(QuestionBase):
    """用于创建新题目的模型，包含选项"""
    choices: Optional[List[ChoiceCreate]] = Field(None, description="题目的选项列表")

class Question(QuestionBase):
    """用于API响应的题目模型"""
    id: int = Field(..., description="题目ID")
    choices: List[Choice] = Field([], description="题目的选项列表")

    class Config:
        from_attributes = True
