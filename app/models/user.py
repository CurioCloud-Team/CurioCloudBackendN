"""
用户数据模型

定义用户相关的数据库表结构
"""
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """
    用户模型
    
    表示系统中的用户账户信息
    """
    __tablename__ = "users"
    
    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="用户唯一标识")
    
    # 用户基本信息
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱地址")
    full_name = Column(String(100), comment="用户全名")
    
    # 认证信息
    hashed_password = Column(String(255), nullable=False, comment="哈希加密后的密码")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="账户是否激活")
    is_verified = Column(Boolean, default=False, comment="邮箱是否已验证")
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        """字符串表示"""
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"