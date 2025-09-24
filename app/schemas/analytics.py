from pydantic import BaseModel
from typing import List, Dict, Any
import uuid

class GradeUploadResponse(BaseModel):
    analysis_id: str
    summary_preview: str # 返回报告的第一行作为预览
    message: str = "文件上传成功，AI正在生成分析报告..."

class AnalysisReportResponse(BaseModel):
    analysis_id: str
    full_report_markdown: str # 完整的Markdown格式报告
    message: str = "报告获取成功"


class AnalysisReportInDB(BaseModel):
    id: int
    analysis_id: str
    user_id: int
    summary: str
    charts_data: Dict[str, Any]
    knowledge_gaps: Dict[str, Any]

    class Config:
        from_attributes = True

class AnalysisReportEntry(BaseModel):
    analysis_id: str
    summary_preview: str
    created_at: str
    message: str = "历史报告条目"
