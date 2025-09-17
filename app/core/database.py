"""
数据库连接和会话管理

使用SQLAlchemy进行数据库操作
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# 创建数据库引擎
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,  # 在使用连接前测试连接是否有效
    pool_recycle=300,    # 每5分钟回收连接
    echo=settings.debug  # 在调试模式下打印SQL语句
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    依赖注入函数，用于FastAPI路由中获取数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """删除数据库表"""
    Base.metadata.drop_all(bind=engine)