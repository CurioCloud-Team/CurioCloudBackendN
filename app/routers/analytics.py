from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.analytics_service import AnalyticsService
from app.schemas.analytics import GradeUploadResponse, AnalysisReportResponse
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
    上传学生成绩Excel文件进行分析。
    - **Request Body**: 需要一个multipart/form-data请求，其中包含一个名为'file'的Excel文件。
    - **Response Body**: 返回一个包含分析ID和初步摘要的JSON对象。
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="无效的文件类型，请上传Excel文件 (.xlsx, .xls)")

    service = AnalyticsService(db)
    report = await service.process_grades_file(file=file, user_id=current_user.id)
    
    return {
        "analysis_id": report.analysis_id,
        "summary": report.summary,
        "message": "文件上传成功，分析已完成"
    }

@router.get("/report/{analysis_id}", response_model=AnalysisReportResponse)
def get_analysis_report(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    根据分析ID获取详细的学情分析报告。
    - **Path Parameter**: `analysis_id` 是上传文件后返回的唯一ID。
    - **Response Body**: 返回包含图表数据和知识点差距分析的完整报告。
    """
    service = AnalyticsService(db)
    report = service.get_analysis_report(analysis_id=analysis_id, user_id=current_user.id)
    
    return {
        "analysis_id": report.analysis_id,
        "summary": report.summary,
        "report": {
            "charts_data": report.charts_data,
            "knowledge_gaps": report.knowledge_gaps
        },
        "message": "报告获取成功"
    }
