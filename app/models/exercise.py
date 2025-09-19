"""
练习题相关的数据模型
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SQLAlchemyEnum, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import enum

class QuestionType(str, enum.Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    SHORT_ANSWER = "short_answer"

class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class Question(Base):
    """
    题目模型
    """
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, comment="题目唯一标识")
    lesson_plan_id = Column(Integer, ForeignKey("lesson_plans.id"), nullable=False, comment="关联教案ID")
    question_type = Column(SQLAlchemyEnum(QuestionType), nullable=False, comment="题目类型")
    difficulty = Column(SQLAlchemyEnum(DifficultyLevel), nullable=False, comment="难度")
    content = Column(Text, nullable=False, comment="题干内容")
    answer = Column(Text, nullable=True, comment="答案解析")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    lesson_plan = relationship("LessonPlan", backref="questions")
    choices = relationship("Choice", back_populates="question", cascade="all, delete-orphan")

class Choice(Base):
    """
    选项模型（主要用于选择题）
    """
    __tablename__ = "choices"

    id = Column(Integer, primary_key=True, index=True, comment="选项唯一标识")
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False, comment="关联题目ID")
    content = Column(Text, nullable=False, comment="选项内容")
    is_correct = Column(Boolean, default=False, nullable=False, comment="是否为正确答案")

    question = relationship("Question", back_populates="choices")
