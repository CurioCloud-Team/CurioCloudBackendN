"""
教学相关的数据验证模式

定义教学设计对话和教案管理的请求/响应数据结构
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class StartConversationRequest(BaseModel):
    """开始对话请求"""
    use_dynamic_mode: Optional[bool] = Field(
        default=True,
        description="是否使用AI动态问题生成模式，默认为True"
    )


class QuestionCard(BaseModel):
    """问题卡片"""
    step_key: str = Field(description="步骤键名")
    question: str = Field(description="问题内容")
    options: List[str] = Field(description="选项列表")
    allows_free_text: bool = Field(description="是否允许自由文本输入")


class StartConversationResponse(BaseModel):
    """开始对话响应"""
    session_id: str = Field(description="会话ID")
    question_card: QuestionCard = Field(description="问题卡片")
    is_dynamic_mode: bool = Field(description="是否为动态模式")


class ProcessAnswerRequest(BaseModel):
    """处理回答请求"""
    session_id: str = Field(description="会话ID")
    answer: str = Field(description="用户回答")


class LessonPlanActivity(BaseModel):
    """教学活动"""
    activity_name: str = Field(description="活动名称")
    description: str = Field(description="活动描述")
    duration: int = Field(description="活动时长（分钟）")
    order_index: int = Field(description="活动顺序")


class LessonPlan(BaseModel):
    """教案"""
    id: int = Field(description="教案ID")
    title: str = Field(description="教案标题")
    subject: str = Field(description="学科")
    grade: str = Field(description="年级")
    teaching_objective: str = Field(description="教学目标")
    teaching_outline: str = Field(description="教学大纲")
    activities: List[LessonPlanActivity] = Field(description="教学活动列表")
    created_at: Optional[datetime] = Field(description="创建时间")
    web_search_info: Optional[Dict[str, Any]] = Field(default=None, description="联网搜索信息")


class ProcessAnswerResponse(BaseModel):
    """处理回答响应"""
    session_id: str = Field(description="会话ID")
    status: str = Field(description="会话状态")
    is_dynamic_mode: bool = Field(description="是否为动态模式")
    question_card: Optional[QuestionCard] = Field(default=None, description="下一个问题卡片")
    lesson_plan: Optional[LessonPlan] = Field(default=None, description="生成的教案")


class LessonPlanListResponse(BaseModel):
    """教案列表响应"""
    id: int = Field(description="教案ID")
    title: str = Field(description="教案标题")
    subject: str = Field(description="学科")
    grade: str = Field(description="年级")
    created_at: datetime = Field(description="创建时间")


class SessionInfo(BaseModel):
    """会话信息"""
    session_id: str = Field(description="会话ID")
    status: str = Field(description="会话状态")
    is_dynamic_mode: bool = Field(description="是否为动态模式")
    question_count: int = Field(description="已提问次数")
    max_questions: int = Field(description="最大提问次数")
    current_step: Optional[str] = Field(description="当前步骤")
    collected_data: Dict[str, Any] = Field(description="收集的数据")
    created_at: datetime = Field(description="创建时间")