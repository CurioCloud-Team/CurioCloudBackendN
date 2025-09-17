"""
用户认证服务

提供用户注册、登录等认证相关的业务逻辑
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from typing import Optional

from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, AuthResponse, Token,
    UserProfileUpdate, UserProfileResponse
)
from app.utils.security import hash_password, verify_password
from app.utils.jwt import create_access_token, get_token_expire_time


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        """
        初始化认证服务
        
        Args:
            db: 数据库会话
        """
        self.db = db
    
    def register_user(self, user_data: UserCreate) -> AuthResponse:
        """
        用户注册
        
        Args:
            user_data: 用户注册数据
            
        Returns:
            认证响应包含用户信息和令牌
            
        Raises:
            HTTPException: 注册失败时抛出异常
        """
        try:
            # 检查用户名是否已存在
            existing_user = self.db.query(User).filter(
                (User.username == user_data.username) | (User.email == user_data.email)
            ).first()
            
            if existing_user:
                if existing_user.username == user_data.username:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="用户名已存在"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="邮箱已被注册"
                    )
            
            # 创建新用户
            hashed_password = hash_password(user_data.password)
            db_user = User(
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password
            )
            
            # 保存到数据库
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            # 生成访问令牌
            access_token = create_access_token(
                data={"sub": db_user.username, "user_id": db_user.id}
            )
            
            # 构建响应
            user_response = UserResponse.from_orm(db_user)
            token = Token(
                access_token=access_token,
                expires_in=get_token_expire_time()
            )
            
            return AuthResponse(
                user=user_response,
                token=token,
                message="注册成功"
            )
            
        except HTTPException:
            # 重新抛出HTTP异常
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            # 检查具体的约束违反类型
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            if "username" in error_msg.lower():
                detail = "用户名已存在"
            elif "email" in error_msg.lower():
                detail = "邮箱已被注册"
            else:
                detail = "用户信息冲突，请检查用户名和邮箱"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )
        except Exception as e:
            self.db.rollback()
            print(f"Unexpected error during registration: {type(e).__name__}: {e}")  # 调试信息
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="注册过程中发生错误"
            )
    
    def login_user(self, login_data: UserLogin) -> AuthResponse:
        """
        用户登录
        
        Args:
            login_data: 用户登录数据
            
        Returns:
            认证响应包含用户信息和令牌
            
        Raises:
            HTTPException: 登录失败时抛出异常
        """
        # 查找用户（支持用户名或邮箱登录）
        user = self.db.query(User).filter(
            (User.username == login_data.username) | (User.email == login_data.username)
        ).first()
        
        # 验证用户存在性和密码
        if not user or not verify_password(login_data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名、邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 检查账户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 生成访问令牌
        access_token = create_access_token(
            data={"sub": user.username, "user_id": user.id}
        )
        
        # 构建响应
        user_response = UserResponse.from_orm(user)
        token = Token(
            access_token=access_token,
            expires_in=get_token_expire_time()
        )
        
        return AuthResponse(
            user=user_response,
            token=token,
            message="登录成功"
        )
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户对象或None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        根据用户ID获取用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户对象或None
        """
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_profile(self, user_id: int) -> UserProfileResponse:
        """
        获取用户资料
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户资料响应
            
        Raises:
            HTTPException: 用户不存在时抛出异常
        """
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        return UserProfileResponse.from_orm(user)
    
    def update_user_profile(self, user_id: int, profile_data: UserProfileUpdate) -> UserProfileResponse:
        """
        更新用户资料
        
        Args:
            user_id: 用户ID
            profile_data: 用户资料更新数据
            
        Returns:
            更新后的用户资料
            
        Raises:
            HTTPException: 更新失败时抛出异常
        """
        try:
            # 获取用户
            user = self.get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="用户不存在"
                )
            
            # 检查邮箱是否已被其他用户使用
            if profile_data.email and profile_data.email != user.email:
                existing_user = self.db.query(User).filter(
                    User.email == profile_data.email,
                    User.id != user_id
                ).first()
                
                if existing_user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="邮箱已被其他用户使用"
                    )
            
            # 更新用户信息
            update_data = profile_data.dict(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            # 保存更改
            self.db.commit()
            self.db.refresh(user)
            
            return UserProfileResponse.from_orm(user)
            
        except HTTPException:
            # 重新抛出HTTP异常
            self.db.rollback()
            raise
        except IntegrityError as e:
            self.db.rollback()
            error_msg = str(e.orig) if hasattr(e, 'orig') else str(e)
            if "email" in error_msg.lower():
                detail = "邮箱已被其他用户使用"
            else:
                detail = "用户信息更新失败，请检查输入数据"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail
            )
        except Exception as e:
            self.db.rollback()
            print(f"Unexpected error during profile update: {type(e).__name__}: {e}")  # 调试信息
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="更新用户资料时发生错误"
            )