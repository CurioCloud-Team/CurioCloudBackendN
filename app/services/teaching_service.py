"""
教学服务模块

处理对话式教学设计的业务逻辑
"""
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified

from app.models import LessonCreationSession, LessonPlan, LessonPlanActivity, SessionStatus
from app.services.ai_service import AIService
from app.conversation_flow import CONVERSATION_FLOW, get_step_config, get_next_step, is_final_step
from app.core.config import settings


class TeachingService:
    """教学服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()

    def start_conversation(self, user_id: int) -> Dict[str, Any]:
        """
        开始新的教学设计对话

        Args:
            user_id: 用户ID

        Returns:
            包含会话ID和第一个问题的字典
        """
        try:
            # 生成会话ID
            session_id = str(uuid.uuid4())

            # 创建新会话
            session = LessonCreationSession(
                session_id=session_id,
                user_id=user_id,
                status=SessionStatus.in_progress,
                current_step=CONVERSATION_FLOW['start_step'],
                collected_data={},
                history=[]
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # 获取第一个问题
            first_question = self._get_question_card(CONVERSATION_FLOW['start_step'])

            return {
                "session_id": session_id,
                "question_card": first_question
            }

        except Exception as e:
            self.db.rollback()
            print(f"开始对话失败: {type(e).__name__}: {e}")
            raise

    async def process_answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        """
        处理用户回答并返回下一步或最终结果

        Args:
            session_id: 会话ID
            answer: 用户回答

        Returns:
            包含下一步问题或最终教案的字典
        """
        try:
            # 获取会话
            session = self.db.query(LessonCreationSession).filter_by(session_id=session_id).first()
            if not session:
                raise ValueError("会话不存在")

            if session.status != SessionStatus.in_progress:
                raise ValueError("会话已完成或失败")

            # 获取当前步骤配置
            current_step_config = get_step_config(session.current_step)
            if not current_step_config:
                raise ValueError("无效的对话步骤")

            # 记录对话历史
            question = self._get_question_card(session.current_step)
            session.history.append({
                "step": session.current_step,
                "question": question['question'],
                "answer": answer
            })
            flag_modified(session, "history")

            # 保存用户回答
            key_to_save = current_step_config['key_to_save']
            session.collected_data[key_to_save] = answer

            # 标记 collected_data 字段已被修改，确保数据库更新
            flag_modified(session, "collected_data")

            # 获取下一步
            next_step = get_next_step(session.current_step)

            if next_step == 'finalize':
                # 流程结束，开始生成教案
                session.status = SessionStatus.processing
                self.db.commit()

                # 直接调用异步AI服务
                lesson_plan_data = await self.ai_service.generate_lesson_plan(session.collected_data)

                if lesson_plan_data:
                    # 保存教案到数据库
                    lesson_plan = self._save_lesson_plan(session.user_id, session.collected_data, lesson_plan_data)
                    session.lesson_plan_id = lesson_plan.id
                    session.status = SessionStatus.completed
                    self.db.commit()

                    return {
                        "session_id": session_id,
                        "status": "completed",
                        "lesson_plan": self._format_lesson_plan_response(lesson_plan)
                    }
                else:
                    session.status = SessionStatus.failed
                    self.db.commit()
                    raise ValueError("教案生成失败")

            else:
                # 更新当前步骤
                session.current_step = next_step
                self.db.commit()

                # 返回下一个问题
                next_question = self._get_question_card(next_step)
                return {
                    "session_id": session_id,
                    "question_card": next_question
                }

        except Exception as e:
            self.db.rollback()
            print(f"处理回答失败: {type(e).__name__}: {e}")
            raise

    def get_lesson_plans(self, user_id: int) -> List[Dict[str, Any]]:
        """
        获取用户的教案列表

        Args:
            user_id: 用户ID

        Returns:
            教案列表
        """
        try:
            lesson_plans = self.db.query(LessonPlan).filter_by(user_id=user_id).all()
            return [self._format_lesson_plan_response(plan) for plan in lesson_plans]
        except Exception as e:
            print(f"获取教案列表失败: {type(e).__name__}: {e}")
            raise

    def get_lesson_plan(self, plan_id: int, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取单个教案详情

        Args:
            plan_id: 教案ID
            user_id: 用户ID

        Returns:
            教案详情字典
        """
        try:
            lesson_plan = self.db.query(LessonPlan).filter_by(id=plan_id, user_id=user_id).first()
            if lesson_plan:
                return self._format_lesson_plan_response(lesson_plan)
            return None
        except Exception as e:
            print(f"获取教案详情失败: {type(e).__name__}: {e}")
            raise

    def delete_lesson_plan(self, plan_id: int, user_id: int) -> bool:
        """
        删除教案

        Args:
            plan_id: 教案ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        try:
            lesson_plan = self.db.query(LessonPlan).filter_by(id=plan_id, user_id=user_id).first()
            if lesson_plan:
                self.db.delete(lesson_plan)
                self.db.commit()
                return True
            return False
        except Exception as e:
            self.db.rollback()
            print(f"删除教案失败: {type(e).__name__}: {e}")
            raise

    def _get_question_card(self, step_key: str) -> Dict[str, Any]:
        """
        获取问题卡片

        Args:
            step_key: 步骤键名

        Returns:
            问题卡片字典
        """
        config = get_step_config(step_key)
        return {
            "step_key": step_key,
            "question": config['question'],
            "options": config['options'],
            "allows_free_text": config['allows_free_text']
        }

    def _save_lesson_plan(self, user_id: int, collected_data: Dict[str, Any], lesson_plan_data: Dict[str, Any]) -> LessonPlan:
        """
        保存教学计划到数据库

        Args:
            user_id: 用户ID
            collected_data: 对话过程中收集的用户数据
            lesson_plan_data: AI服务生成的教学计划核心数据

        Returns:
            保存的LessonPlan对象
        """
        try:
            # 创建教案
            lesson_plan = LessonPlan(
                user_id=user_id,
                title=lesson_plan_data['title'],
                subject=collected_data.get('subject', ''),
                grade=collected_data.get('grade', ''),
                teaching_objective='\n'.join(lesson_plan_data['learning_objectives']),
                teaching_outline=lesson_plan_data['teaching_outline']
            )

            self.db.add(lesson_plan)
            self.db.flush()  # 获取ID但不提交

            # 创建活动
            for activity_data in lesson_plan_data['activities']:
                activity = LessonPlanActivity(
                    lesson_plan_id=lesson_plan.id,
                    activity_name=activity_data['name'],
                    description=activity_data['description'],
                    duration=activity_data['duration'],
                    order_index=activity_data['order']
                )
                self.db.add(activity)

            return lesson_plan

        except Exception as e:
            print(f"保存教案失败: {type(e).__name__}: {e}")
            raise

    def _format_lesson_plan_response(self, lesson_plan: LessonPlan) -> Dict[str, Any]:
        """
        格式化教案响应

        Args:
            lesson_plan: LessonPlan对象

        Returns:
            格式化的响应字典
        """
        activities = []
        for activity in lesson_plan.activities:
            activities.append({
                "activity_name": activity.activity_name,
                "description": activity.description,
                "duration": activity.duration,
                "order_index": activity.order_index
            })

        return {
            "id": lesson_plan.id,
            "title": lesson_plan.title,
            "subject": lesson_plan.subject,
            "grade": lesson_plan.grade,
            "teaching_objective": lesson_plan.teaching_objective,
            "teaching_outline": lesson_plan.teaching_outline,
            "activities": sorted(activities, key=lambda x: x['order_index']),
            "created_at": lesson_plan.created_at.isoformat() if lesson_plan.created_at else None
        }