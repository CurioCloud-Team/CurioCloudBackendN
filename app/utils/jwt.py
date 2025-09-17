"""
JWT令牌管理

提供JWT令牌的生成和验证功能
"""
from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from app.core.config import settings
from app.schemas.user import TokenData


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码到令牌中的数据
        expires_delta: 令牌过期时间增量
        
    Returns:
        JWT令牌字符串
    """
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    
    # 生成JWT令牌
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """
    验证JWT令牌
    
    Args:
        token: JWT令牌字符串
        
    Returns:
        令牌数据或None（如果无效）
    """
    try:
        # 解码JWT令牌
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        
        # 提取用户信息
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        
        if username is None:
            return None
            
        return TokenData(username=username, user_id=user_id)
        
    except JWTError:
        return None


def get_token_expire_time() -> int:
    """
    获取令牌过期时间（秒）
    
    Returns:
        过期时间秒数
    """
    return settings.jwt_access_token_expire_minutes * 60