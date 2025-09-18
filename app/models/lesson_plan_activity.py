"""
教学活动数据模型

定义教学活动相关的数据库表结构
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class LessonPlanActivity(Base):
    """
    教学活动模型

    存储教学计划中的具体活动
    """
    __tablename__ = "lesson_plan_activities"

    # 主键ID
    id = Column(Integer, primary_key=True, index=True, comment="活动唯一标识")

    # 外键关联
    lesson_plan_id = Column(Integer, ForeignKey("lesson_plans.id"), nullable=False, comment="关联教案ID")

    # 活动信息
    activity_name = Column(String(255), nullable=False, comment="活动名称")
    description = Column(Text, comment="活动详细描述")
    duration = Column(Integer, comment="活动时长(分钟)")
    order_index = Column(Integer, nullable=False, comment="活动顺序")

    def __repr__(self):
        """字符串表示"""
        return f"<LessonPlanActivity(id={self.id}, name='{self.activity_name}', duration={self.duration})>"