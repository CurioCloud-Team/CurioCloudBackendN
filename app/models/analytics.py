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
    
    summary = Column(Text, nullable=True, comment="AI生成的自然语言分析摘要")
    charts_data = Column(JSON, nullable=True, comment="用于图表可视化的数据")
    knowledge_gaps = Column(JSON, nullable=True, comment="识别出的知识点差距和教学建议")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")

    owner = relationship("User")
