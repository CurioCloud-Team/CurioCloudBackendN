"""
认证相关的API路由

提供用户注册和登录的RESTful API接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.user import UserCreate, UserLogin, AuthResponse, MessageResponse
from app.services.auth_service import AuthService

# 创建认证路由器
router = APIRouter(
    prefix="/api/auth",
    tags=["认证"],
    responses={
        404: {"description": "未找到"},
        422: {"description": "请求数据验证失败"}
    }
)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户，成功后返回用户信息和访问令牌"
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> AuthResponse:
    """
    用户注册接口
    
    Args:
        user_data: 用户注册信息
        db: 数据库会话
        
    Returns:
        包含用户信息和访问令牌的认证响应
        
    Raises:
        HTTPException: 注册失败时抛出相应的HTTP异常
    """
    try:
        auth_service = AuthService(db)
        return auth_service.register_user(user_data)
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册服务暂时不可用，请稍后重试"
        )


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="用户登录",
    description="使用用户名/邮箱和密码进行身份验证，成功后返回用户信息和访问令牌"
)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> AuthResponse:
    """
    用户登录接口
    
    Args:
        login_data: 用户登录信息
        db: 数据库会话
        
    Returns:
        包含用户信息和访问令牌的认证响应
        
    Raises:
        HTTPException: 登录失败时抛出相应的HTTP异常
    """
    try:
        auth_service = AuthService(db)
        return auth_service.login_user(login_data)
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        # 处理未预期的异常
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录服务暂时不可用，请稍后重试"
        )


@router.get(
    "/health",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="健康检查",
    description="检查认证服务是否正常运行"
)
async def health_check() -> MessageResponse:
    """
    认证服务健康检查接口
    
    Returns:
        服务状态消息
    """
    return MessageResponse(
        message="认证服务运行正常",
        success=True
    )