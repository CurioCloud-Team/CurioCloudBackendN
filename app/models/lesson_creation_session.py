"""
教学会话数据模型

定义教学设计对话会话相关的数据库表结构
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, ForeignKey, JSON, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class SessionStatus(enum.Enum):
    """会话状态枚举"""
    in_progress = "in_progress"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class LessonCreationSession(Base):
    """
    教学设计会话模型

    存储用户与系统进行对话式教学设计的会话状态
    """
    __tablename__ = "lesson_creation_sessions"

    # 主键ID
    session_id = Column(String(36), primary_key=True, index=True, comment="会话唯一标识(UUID)")

    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="关联用户ID")
    lesson_plan_id = Column(Integer, ForeignKey("lesson_plans.id"), nullable=True, comment="关联教案ID")

    # 会话状态
    status = Column(Enum(SessionStatus), default=SessionStatus.in_progress, comment="会话状态")

    # 对话进度
    current_step = Column(String(50), comment="当前对话步骤的键")
    ai_questions_asked = Column(Integer, default=0, comment="已提问的问题数量")
    max_ai_questions = Column(Integer, default=5, comment="最大问题数量")

    # 收集的数据
    collected_data = Column(JSON, default=dict, comment="已收集的用户回答数据")
    history = Column(JSON, nullable=False, comment="存储对话历史记录")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    user = relationship("User", backref="lesson_sessions")
    lesson_plan = relationship("LessonPlan", backref="lesson_creation_session")

    def __repr__(self):
        """字符串表示"""
        return f"<LessonCreationSession(session_id='{self.session_id}', user_id={self.user_id}, status={self.status.value})>"