"""
用户管理路由

提供用户资料相关的API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserProfileResponse, UserProfileUpdate, MessageResponse
from app.services.auth_service import AuthService


# 创建路由器
router = APIRouter(
    prefix="/api/user",
    tags=["用户管理"],
    responses={
        401: {"description": "未认证"},
        403: {"description": "权限不足"},
        404: {"description": "用户不存在"}
    }
)


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="获取用户资料",
    description="获取当前登录用户的资料信息"
)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    """
    获取用户资料
    
    获取当前登录用户的完整资料信息，包括：
    - 用户基本信息（用户名、邮箱、全名）
    - 账户状态（是否激活、是否验证）
    - 时间戳（创建时间、更新时间）
    
    Returns:
        UserProfileResponse: 用户资料信息
        
    Raises:
        401: 未提供有效的认证令牌
        404: 用户不存在
    """
    auth_service = AuthService(db)
    return auth_service.get_user_profile(current_user.id)


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="更新用户资料",
    description="更新当前登录用户的资料信息"
)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserProfileResponse:
    """
    更新用户资料
    
    允许用户更新以下信息：
    - 全名 (full_name): 可选，最大100个字符
    - 邮箱 (email): 可选，必须是有效的邮箱格式，且不能与其他用户重复
    
    注意：
    - 用户名 (username) 不允许修改
    - 只有提供的字段会被更新，未提供的字段保持不变
    - 邮箱更新时会检查重复性
    
    Args:
        profile_data: 用户资料更新数据
        
    Returns:
        UserProfileResponse: 更新后的用户资料信息
        
    Raises:
        400: 邮箱已被其他用户使用或数据验证失败
        401: 未提供有效的认证令牌
        404: 用户不存在
        500: 服务器内部错误
    """
    auth_service = AuthService(db)
    return auth_service.update_user_profile(current_user.id, profile_data)


@router.get(
    "/profile/status",
    response_model=MessageResponse,
    summary="获取用户状态",
    description="获取当前用户的账户状态信息"
)
async def get_user_status(
    current_user: User = Depends(get_current_active_user)
) -> MessageResponse:
    """
    获取用户状态
    
    返回当前用户的账户状态概要信息
    
    Returns:
        MessageResponse: 包含用户状态信息的响应
        
    Raises:
        401: 未提供有效的认证令牌
    """
    status_parts = []
    
    if current_user.is_active:
        status_parts.append("账户已激活")
    else:
        status_parts.append("账户已禁用")
    
    if current_user.is_verified:
        status_parts.append("邮箱已验证")
    else:
        status_parts.append("邮箱未验证")
    
    status_message = f"用户 {current_user.username}: {', '.join(status_parts)}"
    
    return MessageResponse(
        message=status_message,
        success=True
    )