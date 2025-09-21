import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class PptTaskStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PptGenerationTask(Base):
    __tablename__ = "ppt_generation_tasks"
    __table_args__ = {'comment': 'PPT生成任务表'}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="用户ID")
    lesson_plan_id = Column(Integer, ForeignKey("lesson_plans.id"), nullable=True, comment="关联的教案ID")
    sid = Column(String(255), unique=True, index=True, nullable=False, comment="讯飞API返回的任务SID")
    status = Column(SAEnum(PptTaskStatus), nullable=False, default=PptTaskStatus.PENDING, comment="任务状态")
    
    created_at = Column(DateTime, server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")

    user = relationship("User")
    lesson_plan = relationship("LessonPlan")
