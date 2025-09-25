"""
练习题生成的API路由
"""
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.services.exercise_service import ExerciseService
from app.schemas.exercise import Question as QuestionSchema
from app.models.user import User
from app.models.exercise import DifficultyLevel

router = APIRouter(
    prefix="/api/exercises",
    tags=["Exercises"],
    responses={404: {"description": "Not found"}},
)

class GenerateMCQRequest(BaseModel):
    num_questions: int = 5
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

@router.post("/lesson-plan/{plan_id}/generate-multiple-choice", response_model=List[QuestionSchema])
async def generate_multiple_choice_questions(
    plan_id: int,
    request: GenerateMCQRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为指定的教案生成选择题
    """
    service = ExerciseService(db)
    questions = await service.generate_and_save_mcq(
        lesson_plan_id=plan_id,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value,
    )
    return questions

class GenerateFITBRequest(BaseModel):
    num_questions: int = 5
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

@router.post("/lesson-plan/{plan_id}/generate-fill-in-the-blank", response_model=List[QuestionSchema])
async def generate_fill_in_the_blank_questions(
    plan_id: int,
    request: GenerateFITBRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为指定的教案生成填空题
    """
    service = ExerciseService(db)
    questions = await service.generate_and_save_fitb(
        lesson_plan_id=plan_id,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value,
    )
    return questions

class GenerateSAQRequest(BaseModel):
    num_questions: int = 5
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

@router.post("/lesson-plan/{plan_id}/generate-short-answer", response_model=List[QuestionSchema])
async def generate_short_answer_questions(
    plan_id: int,
    request: GenerateSAQRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为指定的教案生成简答题
    """
    service = ExerciseService(db)
    questions = await service.generate_and_save_saq(
        lesson_plan_id=plan_id,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value,
    )
    return questions

@router.get("/lesson-plan/{plan_id}", response_model=List[QuestionSchema])
def get_exercises_for_lesson_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取指定教案的所有练习题
    """
    service = ExerciseService(db)
    questions = service.get_exercises_by_lesson_plan_id(lesson_plan_id=plan_id)
    return questions
