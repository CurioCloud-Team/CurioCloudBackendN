from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import GradeUploadResponse, AnalysisReportResponse, AnalysisReportEntry
from typing import List
from app.models.user import User
from app.dependencies.auth import get_current_active_user

router = APIRouter()

@router.post("/upload_grades", response_model=GradeUploadResponse)
async def upload_grades_for_analysis(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    file: UploadFile = File(...)
):
    """
    上传任何学生相关的Excel文件进行智能分析。
    - **Request Body**: 需要一个multipart/form-data请求，其中包含一个名为'file'的Excel文件。
    - **Response Body**: 返回一个包含分析ID和报告预览的JSON对象。
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="无效的文件类型，请上传Excel文件 (.xlsx, .xls)")

    service = AnalyticsService(db)
    report = await service.process_grades_file(file=file, user_id=current_user.id)
    
    # 提取报告的第一行作为预览
    summary_preview = report.summary.split('\n')[0].replace('#', '').strip()

    return {
        "analysis_id": report.analysis_id,
        "summary_preview": summary_preview,
        "message": "文件上传成功，AI分析已完成"
    }

@router.get("/report/{analysis_id}", response_model=AnalysisReportResponse)
def get_analysis_report(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据分析ID获取完整的叙事性学情分析报告。
    - **Path Parameter**: `analysis_id` 是上传文件后返回的唯一ID。
    - **Response Body**: 返回包含完整Markdown格式报告的JSON对象。
    """
    service = AnalyticsService(db)
    report_data = service.get_analysis_report(analysis_id=analysis_id, user_id=current_user.id)
    
    return {
        "analysis_id": report_data["analysis_id"],
        "full_report_markdown": report_data["summary"],
        "message": "报告获取成功"
    }


@router.get("/reports", response_model=List[AnalysisReportEntry])
def get_all_user_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取当前用户的所有历史分析报告列表。
    - **Response Body**: 返回一个包含所有历史报告摘要的列表。
    """
    service = AnalyticsService(db)
    reports = service.get_all_analysis_reports_for_user(user_id=current_user.id)
    return reports
