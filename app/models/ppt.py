"""
PPT生成任务数据库模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class PPTGenerationTask(Base):
    __tablename__ = "ppt_generation_tasks"
    __table_args__ = {'comment': 'PPT生成任务表'}

    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    task_id = Column(String(255), index=True, unique=True, nullable=True, comment="讯飞API返回的任务ID (sid)")
    status = Column(String(50), default="pending", comment="任务状态 (pending, processing, done, failed)")
    ppt_url = Column(String(1024), nullable=True, comment="生成的PPT下载链接")
    query = Column(Text, nullable=False, comment="用户输入的关键词或内容")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("User")
