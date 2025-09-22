"""
教案数据模型

定义教学计划相关的数据库表结构
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class LessonPlan(Base):
    """
    教学计划模型

    存储AI生成的完整教学计划
    """
    __tablename__ = "lesson_plans"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="教案唯一标识")

    # 外键关联
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="关联用户ID")

    # 基本信息
    title = Column(String(255), nullable=False, comment="AI生成的标题")
    subject = Column(String(100), nullable=False, comment="学科")
    grade = Column(String(100), nullable=False, comment="年级")

    # 教学内容
    teaching_objective = Column(Text, comment="学习目标")
    teaching_outline = Column(Text, comment="教学大纲/简介")

    # 联网搜索信息
    web_search_info = Column(JSON, comment="联网搜索结果信息")

    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")

    # 关联关系
    user = relationship("User", backref="lesson_plans")
    activities = relationship("LessonPlanActivity", backref="lesson_plan", cascade="all, delete-orphan")

    def __repr__(self):
        """字符串表示"""
        return f"<LessonPlan(id={self.id}, title='{self.title}', subject='{self.subject}')>"