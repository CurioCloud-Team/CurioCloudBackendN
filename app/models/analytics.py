import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.dialects.mysql import JSON

from app.core.database import Base

class AnalysisReport(Base):
    __tablename__ = "analysis_reports"
    __table_args__ = {'comment': '学情分析报告表'}

    id = Column(Integer, primary_key=True, index=True, comment="报告ID")
    analysis_id = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), comment="用于API交互的唯一ID")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="上传该报告的用户ID")
    
    summary = Column(Text, nullable=True, comment="AI生成的完整叙事性分析报告（Markdown格式）")
    
    # 以下字段将被废弃，但暂时保留以兼容旧数据
    charts_data = Column(JSON, nullable=True, comment="[已废弃] 用于图表可视化的数据")
    knowledge_gaps = Column(JSON, nullable=True, comment="[已废弃] 识别出的知识点差距和教学建议")
    average_score = Column(String(10), nullable=True, comment="[已废弃] 班级平均分")
    failing_students_count = Column(Integer, nullable=True, comment="[已废弃] 不及格学生人数")
    failing_students_list = Column(JSON, nullable=True, comment="[已废弃] 不及格学生名单")
    knowledge_point_error_rates = Column(JSON, nullable=True, comment="[已废弃] 各知识点错误率")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    owner = relationship("User")
