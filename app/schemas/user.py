"""
用户相关的数据验证模式

使用Pydantic定义请求和响应的数据格式
"""
from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional
import re


class UserBase(BaseModel):
    """用户基础模式"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: Optional[str] = Field(None, max_length=100, description="用户全名")
    
    @validator('username')
    def validate_username(cls, v):
        """验证用户名格式"""
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v


class UserCreate(UserBase):
    """用户注册请求模式"""
    password: str = Field(..., min_length=8, max_length=100, description="密码")
    confirm_password: str = Field(..., description="确认密码")
    
    @validator('password')
    def validate_password(cls, v):
        """验证密码强度"""
        if not re.search(r'[A-Za-z]', v):
            raise ValueError('密码必须包含至少一个字母')
        if not re.search(r'\d', v):
            raise ValueError('密码必须包含至少一个数字')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('密码必须包含至少一个特殊字符')
        return v
    
    @validator('confirm_password')
    def validate_passwords_match(cls, v, values):
        """验证密码确认"""
        if 'password' in values and v != values['password']:
            raise ValueError('两次输入的密码不一致')
        return v


class UserLogin(BaseModel):
    """用户登录请求模式"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class UserResponse(BaseModel):
    """用户响应模式"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic配置"""
        from_attributes = True  # 允许从ORM对象创建


class UserInDB(UserBase):
    """数据库中的用户模式"""
    id: int
    hashed_password: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        """Pydantic配置"""
        from_attributes = True


class Token(BaseModel):
    """JWT令牌响应模式"""
    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(..., description="过期时间(秒)")


class TokenData(BaseModel):
    """JWT令牌数据模式"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class AuthResponse(BaseModel):
    """认证成功响应模式"""
    user: UserResponse
    token: Token
    message: str = Field(default="认证成功", description="响应消息")


class MessageResponse(BaseModel):
    """通用消息响应模式"""
    message: str = Field(..., description="响应消息")
    success: bool = Field(default=True, description="操作是否成功")