from pydantic import BaseModel
from typing import List, Dict, Any
import uuid

class GradeUploadResponse(BaseModel):
    analysis_id: str
    summary: str
    message: str = "文件上传成功并已开始分析"

class ReportData(BaseModel):
    charts_data: List[Dict[str, Any]]
    knowledge_gaps: List[Dict[str, Any]]

class AnalysisReportResponse(BaseModel):
    analysis_id: str
    summary: str
    report: ReportData
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
