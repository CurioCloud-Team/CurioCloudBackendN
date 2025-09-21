"""
PPT生成相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class PPTTaskCreate(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="用于生成PPT的关键词或文本内容")
    template_id: Optional[str] = Field("20240718489569D", description="PPT模板ID")
    author: Optional[str] = Field("CurioCloud", description="PPT作者")
    is_card_note: bool = Field(True, description="是否生成PPT演讲备注")
    search: bool = Field(False, description="是否联网搜索")
    is_figure: bool = Field(True, description="是否自动配图")
    ai_image: str = Field("normal", description="AI配图类型: normal 或 advanced")

class PPTTaskStatus(BaseModel):
    id: int
    task_id: Optional[str]
    status: str
    ppt_url: Optional[str]
    query: str
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PPTTaskResponse(BaseModel):
    message: str
    task: PPTTaskStatus
