"""
PPT生成API路由
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.dependencies.auth import get_current_active_user
from app.services.ppt_service import PPTService
from app.schemas.ppt import PPTTaskCreate, PPTTaskStatus, PPTTaskResponse
from app.models.user import User

router = APIRouter(
    prefix="/api/ppt",
    tags=["PPT Generation"],
    responses={404: {"description": "Not found"}},
)

@router.post("/generate", response_model=PPTTaskResponse, status_code=202)
async def generate_ppt(
    ppt_data: PPTTaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    异步启动一个PPT生成任务。

    - **query**: 用于生成PPT的文本内容。
    - **template_id**: (可选) 使用的模板ID。
    """
    ppt_service = PPTService(db)
    task = await ppt_service.create_ppt_task(current_user.id, ppt_data, background_tasks)
    return {"message": "PPT生成任务已启动", "task": task}

@router.get("/status/{task_id}", response_model=PPTTaskStatus)
def get_ppt_status(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取特定PPT生成任务的状态。
    """
    ppt_service = PPTService(db)
    task = ppt_service.get_task_status(task_id, current_user.id)
    return task
