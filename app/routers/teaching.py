"""
教学相关的API路由

提供对话式教学设计和教案管理的RESTful API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.services.teaching_service import TeachingService
from app.schemas.user import MessageResponse
from app.schemas.teaching import (
    StartConversationRequest,
    StartConversationResponse,
    ProcessAnswerRequest,
    ProcessAnswerResponse,
    LessonPlanListResponse,
    LessonPlan
)

# 创建教学路由器
router = APIRouter(
    prefix="/api/teaching",
    tags=["教学"],
    responses={
        404: {"description": "未找到"},
        422: {"description": "请求数据验证失败"}
    }
)


# 删除旧的类定义，因为已经移到schemas中
# class StartConversationRequest:
# class StartConversationResponse:
# class ProcessAnswerRequest:
# class QuestionCard:
# class LessonPlanActivityResponse:
# class LessonPlanResponse:
# class ConversationResponse:


@router.post(
    "/conversational/start",
    response_model=StartConversationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="开始新备课会话",
    description="初始化一个新的备课流程，创建会话记录并返回第一个问题。支持传统固定流程和AI动态问题生成两种模式"
)
async def start_conversation(
    request: StartConversationRequest = StartConversationRequest(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> StartConversationResponse:
    """
    开始新的教学设计对话

    Args:
        request: 包含use_dynamic_mode参数的请求体
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        包含会话ID、问题卡片和模式信息的响应
    """
    try:
        teaching_service = TeachingService(db)
        result = teaching_service.start_conversation(current_user.id, request.use_dynamic_mode)

        return StartConversationResponse(
            session_id=result["session_id"],
            question_card=result["question_card"],
            is_dynamic_mode=result["is_dynamic_mode"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="开始对话失败，请稍后重试"
        )


@router.post(
    "/conversational/next",
    response_model=ProcessAnswerResponse,
    status_code=status.HTTP_200_OK,
    summary="提交回答并获取下一步",
    description="接收用户对上一个问题的回答，更新会话状态，并返回下一个问题或最终生成的教案。支持传统固定流程和AI动态问题生成两种模式"
)
async def process_answer(
    request: ProcessAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> ProcessAnswerResponse:
    """
    处理用户回答

    Args:
        request: 包含session_id和answer的请求体
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        下一个问题或最终教案的响应，包含模式信息
    """
    try:
        teaching_service = TeachingService(db)
        result = await teaching_service.process_answer(request.session_id, request.answer)

        return ProcessAnswerResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理回答失败，请稍后重试"
        )


@router.get(
    "/lesson-plans",
    response_model=List[LessonPlanListResponse],
    status_code=status.HTTP_200_OK,
    summary="获取教案列表",
    description="获取当前用户的所有教案列表"
)
async def get_lesson_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[LessonPlanListResponse]:
    """
    获取用户的教案列表

    Args:
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        教案列表
    """
    try:
        teaching_service = TeachingService(db)
        lesson_plans = teaching_service.get_lesson_plans(current_user.id)
        
        return [LessonPlanListResponse(**plan) for plan in lesson_plans]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取教案列表失败，请稍后重试"
        )


@router.get(
    "/lesson-plans/{plan_id}",
    response_model=LessonPlan,
    status_code=status.HTTP_200_OK,
    summary="获取单个教案详情",
    description="获取指定教案的详细信息"
)
async def get_lesson_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> LessonPlan:
    """
    获取单个教案详情

    Args:
        plan_id: 教案ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        教案详情
    """
    try:
        teaching_service = TeachingService(db)
        lesson_plan = teaching_service.get_lesson_plan(plan_id, current_user.id)

        if not lesson_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="教案不存在"
            )

        return LessonPlan(**lesson_plan)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取教案详情失败，请稍后重试"
        )


@router.delete(
    "/lesson-plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除教案",
    description="删除指定的教案"
)
async def delete_lesson_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除教案

    Args:
        plan_id: 教案ID
        current_user: 当前登录用户
        db: 数据库会话
    """
    try:
        teaching_service = TeachingService(db)
        success = teaching_service.delete_lesson_plan(plan_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="教案不存在"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除教案失败，请稍后重试"
        )