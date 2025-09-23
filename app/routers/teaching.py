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
from app.services.landppt_service import LandPPTService
from app.schemas.user import MessageResponse
from app.schemas.teaching import (
    StartConversationRequest,
    StartConversationResponse,
    ProcessAnswerRequest,
    ProcessAnswerResponse,
    LessonPlanListResponse,
    LessonPlan,
    PPTGenerationResponse,
    PPTStatusResponse,
    PPTSlidesResponse
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


# PPT生成功能路由

@router.post(
    "/lesson-plans/{plan_id}/generate-ppt",
    response_model=PPTGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="从教案生成PPT",
    description="将指定的教案发送给LandPPT服务生成对应的PPT课件"
)
async def generate_ppt_from_lesson_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> PPTGenerationResponse:
    """
    从教案生成PPT

    Args:
        plan_id: 教案ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        生成结果消息
    """
    try:
        # 获取教案
        teaching_service = TeachingService(db)
        lesson_plan = teaching_service.get_lesson_plan(plan_id, current_user.id)

        if not lesson_plan:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="教案不存在"
            )

        # 调用LandPPT服务生成PPT
        landppt_service = LandPPTService()
        result = await landppt_service.create_ppt_from_lesson_plan(lesson_plan)

        return PPTGenerationResponse(**result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PPT生成失败，请稍后重试"
        )


@router.get(
    "/ppt/{ppt_project_id}/status",
    response_model=PPTStatusResponse,
    summary="获取PPT生成状态",
    description="查询LandPPT中PPT项目的生成状态和进度"
)
async def get_ppt_generation_status(
    ppt_project_id: str,
    current_user: User = Depends(get_current_user)
) -> PPTStatusResponse:
    """
    获取PPT生成状态

    Args:
        ppt_project_id: PPT项目ID
        current_user: 当前登录用户

    Returns:
        PPT状态信息
    """
    try:
        landppt_service = LandPPTService()
        status_info = await landppt_service.get_ppt_status(ppt_project_id)

        return PPTStatusResponse(
            ppt_project_id=ppt_project_id,
            status=status_info
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取PPT状态失败，请稍后重试"
        )


@router.get(
    "/ppt/{ppt_project_id}/slides",
    response_model=PPTSlidesResponse,
    summary="获取PPT幻灯片内容",
    description="获取已生成的PPT幻灯片内容和数据"
)
async def get_ppt_slides(
    ppt_project_id: str,
    current_user: User = Depends(get_current_user)
) -> PPTSlidesResponse:
    """
    获取PPT幻灯片内容

    Args:
        ppt_project_id: PPT项目ID
        current_user: 当前登录用户

    Returns:
        PPT幻灯片数据
    """
    try:
        landppt_service = LandPPTService()
        slides_data = await landppt_service.get_ppt_slides(ppt_project_id)

        return PPTSlidesResponse(**slides_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取PPT幻灯片失败，请稍后重试"
        )


@router.get(
    "/ppt/{ppt_project_id}/export/{export_format}",
    summary="导出PPT文件",
    description="将生成的PPT导出为PDF或PPTX格式文件"
)
async def export_ppt_file(
    ppt_project_id: str,
    export_format: str,
    current_user: User = Depends(get_current_user)
):
    """
    导出PPT文件

    Args:
        ppt_project_id: PPT项目ID
        export_format: 导出格式 (pdf 或 pptx)
        current_user: 当前登录用户

    Returns:
        文件下载响应
    """
    try:
        if export_format not in ["pdf", "pptx"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不支持的导出格式，仅支持 pdf 和 pptx"
            )

        landppt_service = LandPPTService()
        file_data = await landppt_service.export_ppt(ppt_project_id, export_format)

        # 返回文件响应
        from fastapi.responses import Response

        content_type = "application/pdf" if export_format == "pdf" else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        filename = f"lesson_plan_{ppt_project_id}.{export_format}"

        return Response(
            content=file_data,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PPT导出失败，请稍后重试"
        )