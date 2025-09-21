"""
会话管理相关的API路由

提供教学设计会话的状态查询和管理功能
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.dependencies.auth import get_current_user
from app.models import User
from app.services.teaching_service import TeachingService
from app.schemas.teaching import SessionInfo

# 创建会话路由器
router = APIRouter(
    prefix="/api/sessions",
    tags=["会话管理"],
    responses={
        404: {"description": "未找到"},
        422: {"description": "请求数据验证失败"}
    }
)


@router.get(
    "/active",
    response_model=List[SessionInfo],
    status_code=status.HTTP_200_OK,
    summary="获取活跃会话列表",
    description="获取当前用户的所有活跃教学设计会话"
)
async def get_active_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[SessionInfo]:
    """
    获取用户的活跃会话列表

    Args:
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        活跃会话列表
    """
    try:
        teaching_service = TeachingService(db)
        sessions = teaching_service.get_active_sessions(current_user.id)
        
        return [SessionInfo(**session) for session in sessions]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败，请稍后重试"
        )


@router.get(
    "/{session_id}",
    response_model=SessionInfo,
    status_code=status.HTTP_200_OK,
    summary="获取会话详情",
    description="获取指定会话的详细信息"
)
async def get_session_info(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> SessionInfo:
    """
    获取会话详情

    Args:
        session_id: 会话ID
        current_user: 当前登录用户
        db: 数据库会话

    Returns:
        会话详情
    """
    try:
        teaching_service = TeachingService(db)
        session_info = teaching_service.get_session_info(session_id, current_user.id)

        if not session_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

        return SessionInfo(**session_info)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话详情失败，请稍后重试"
        )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除会话",
    description="删除指定的教学设计会话"
)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    删除会话

    Args:
        session_id: 会话ID
        current_user: 当前登录用户
        db: 数据库会话
    """
    try:
        teaching_service = TeachingService(db)
        success = teaching_service.delete_session(session_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除会话失败，请稍后重试"
        )