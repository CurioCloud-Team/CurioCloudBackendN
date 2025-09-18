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

# 创建教学路由器
router = APIRouter(
    prefix="/api/teaching",
    tags=["教学"],
    responses={
        404: {"description": "未找到"},
        422: {"description": "请求数据验证失败"}
    }
)


# 请求/响应模型
class StartConversationRequest:
    """开始对话请求（空请求体）"""
    pass


class StartConversationResponse:
    """开始对话响应"""
    def __init__(self, session_id: str, question_card: dict):
        self.session_id = session_id
        self.question_card = question_card


class ProcessAnswerRequest:
    """处理回答请求"""
    def __init__(self, session_id: str, answer: str):
        self.session_id = session_id
        self.answer = answer


class QuestionCard:
    """问题卡片"""
    def __init__(self, step_key: str, question: str, options: List[str], allows_free_text: bool):
        self.step_key = step_key
        self.question = question
        self.options = options
        self.allows_free_text = allows_free_text


class LessonPlanActivityResponse:
    """教学活动响应"""
    def __init__(self, activity_name: str, description: str, duration: int, order_index: int):
        self.activity_name = activity_name
        self.description = description
        self.duration = duration
        self.order_index = order_index


class LessonPlanResponse:
    """教案响应"""
    def __init__(self, id: int, title: str, subject: str, grade: str,
                 teaching_objective: str, teaching_outline: str,
                 activities: List[LessonPlanActivityResponse], created_at: str = None):
        self.id = id
        self.title = title
        self.subject = subject
        self.grade = grade
        self.teaching_objective = teaching_objective
        self.teaching_outline = teaching_outline
        self.activities = activities
        self.created_at = created_at


class ConversationResponse:
    """对话响应"""
    def __init__(self, session_id: str, question_card: QuestionCard = None,
                 status: str = None, lesson_plan: LessonPlanResponse = None):
        self.session_id = session_id
        self.question_card = question_card
        self.status = status
        self.lesson_plan = lesson_plan


@router.post(
    "/conversational/start",
    status_code=status.HTTP_201_CREATED,
    summary="开始新备课会话",
    description="初始化一个新的备课流程，创建会话记录并返回第一个问题"
)
async def start_conversation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    开始新的教学设计对话

    Args:
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        包含会话ID和第一个问题的响应
    """
    try:
        teaching_service = TeachingService(db)
        result = teaching_service.start_conversation(current_user.id)

        return {
            "session_id": result["session_id"],
            "question_card": result["question_card"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="开始对话失败，请稍后重试"
        )


@router.post(
    "/conversational/next",
    status_code=status.HTTP_200_OK,
    summary="提交回答并获取下一步",
    description="接收用户对上一个问题的回答，更新会话状态，并返回下一个问题或最终生成的教案"
)
async def process_answer(
    request: dict,  # 使用dict来接收JSON请求体
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    处理用户回答

    Args:
        request: 包含session_id和answer的请求体
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        下一个问题或最终教案的响应
    """
    try:
        session_id = request.get("session_id")
        answer = request.get("answer")

        if not session_id or not answer:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少必需参数：session_id 或 answer"
            )

        teaching_service = TeachingService(db)
        result = teaching_service.process_answer(session_id, answer)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理回答失败，请稍后重试"
        )


@router.get(
    "/lesson-plans",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="获取教案列表",
    description="获取当前用户的所有教案列表"
)
async def get_lesson_plans(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
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
        return teaching_service.get_lesson_plans(current_user.id)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取教案列表失败，请稍后重试"
        )


@router.get(
    "/lesson-plans/{plan_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="获取单个教案详情",
    description="获取指定教案的详细信息"
)
async def get_lesson_plan(
    plan_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
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

        return lesson_plan

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