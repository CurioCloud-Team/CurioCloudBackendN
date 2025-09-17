"""
认证依赖

提供JWT令牌验证和用户认证的依赖函数
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import Optional

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.user import TokenData


# HTTP Bearer 认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前用户
    
    从JWT令牌中解析用户信息并验证
    
    Args:
        credentials: HTTP Bearer 认证凭据
        db: 数据库会话
        
    Returns:
        当前用户对象
        
    Raises:
        HTTPException: 令牌无效或用户不存在时抛出401异常
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证用户凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 解码JWT令牌
        payload = jwt.decode(
            credentials.credentials, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        # 提取用户名和用户ID
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None or user_id is None:
            raise credentials_exception
            
        token_data = TokenData(username=username, user_id=user_id)
        
    except JWTError:
        raise credentials_exception
    
    # 从数据库获取用户
    user = db.query(User).filter(User.id == token_data.user_id).first()
    if user is None:
        raise credentials_exception
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    获取当前活跃用户
    
    验证用户账户是否处于活跃状态
    
    Args:
        current_user: 当前用户对象
        
    Returns:
        当前活跃用户对象
        
    Raises:
        HTTPException: 用户账户非活跃状态时抛出400异常
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="账户已被禁用"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    获取可选的当前用户
    
    类似get_current_user但不强制要求认证，用于可选认证的接口
    
    Args:
        credentials: HTTP Bearer 认证凭据（可选）
        db: 数据库会话
        
    Returns:
        当前用户对象或None
    """
    if credentials is None:
        return None
    
    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None