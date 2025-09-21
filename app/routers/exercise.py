"""
练习题生成的API路由
"""
from fastapi import APIRouter, Depends, Body, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.services.exercise_service import ExerciseService
from app.schemas.exercise import Question as QuestionSchema
from app.models.user import User
from app.models.exercise import DifficultyLevel

# 创建练习题API路由器
router = APIRouter(
    prefix="/api/exercises",
    tags=["练习题"],
    responses={404: {"description": "未找到"}},
)

class GenerateMCQRequest(BaseModel):
    """生成选择题的请求体模型"""
    num_questions: int = Field(5, gt=0, le=10, description="要生成的题目数量")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="题目难度")

@router.post(
    "/lesson-plan/{plan_id}/generate-multiple-choice", 
    response_model=List[QuestionSchema],
    summary="为教案生成选择题",
    status_code=status.HTTP_201_CREATED
)
async def generate_multiple_choice_questions(
    plan_id: int,
    request: GenerateMCQRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为指定的教案异步生成并保存选择题。

    - **plan_id**: 目标教案的ID。
    - **request**: 包含题目数量和难度的请求体。
    - **需要认证**: 用户必须登录才能访问此端点。
    """
    service = ExerciseService(db)
    questions = await service.generate_and_save_mcq(
        lesson_plan_id=plan_id,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value,
    )
    return questions

class GenerateFITBRequest(BaseModel):
    """生成填空题的请求体模型"""
    num_questions: int = Field(5, gt=0, le=10, description="要生成的题目数量")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="题目难度")

@router.post(
    "/lesson-plan/{plan_id}/generate-fill-in-the-blank", 
    response_model=List[QuestionSchema],
    summary="为教案生成填空题",
    status_code=status.HTTP_201_CREATED
)
async def generate_fill_in_the_blank_questions(
    plan_id: int,
    request: GenerateFITBRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为指定的教案异步生成并保存填空题。

    - **plan_id**: 目标教案的ID。
    - **request**: 包含题目数量和难度的请求体。
    - **需要认证**: 用户必须登录才能访问此端点。
    """
    service = ExerciseService(db)
    questions = await service.generate_and_save_fitb(
        lesson_plan_id=plan_id,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value,
    )
    return questions

class GenerateSAQRequest(BaseModel):
    """生成简答题的请求体模型"""
    num_questions: int = Field(5, gt=0, le=5, description="要生成的题目数量")
    difficulty: DifficultyLevel = Field(DifficultyLevel.MEDIUM, description="题目难度")

@router.post(
    "/lesson-plan/{plan_id}/generate-short-answer", 
    response_model=List[QuestionSchema],
    summary="为教案生成简答题",
    status_code=status.HTTP_201_CREATED
)
async def generate_short_answer_questions(
    plan_id: int,
    request: GenerateSAQRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为指定的教案异步生成并保存简答题。

    - **plan_id**: 目标教案的ID。
    - **request**: 包含题目数量和难度的请求体。
    - **需要认证**: 用户必须登录才能访问此端点。
    """
    service = ExerciseService(db)
    questions = await service.generate_and_save_saq(
        lesson_plan_id=plan_id,
        num_questions=request.num_questions,
        difficulty=request.difficulty.value,
    )
    return questions
