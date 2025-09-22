"""
教学服务模块

处理对话式教学设计的业务逻辑
"""
import uuid
import traceback
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.attributes import flag_modified
from fastapi import HTTPException, status

from app.models import LessonCreationSession, LessonPlan, LessonPlanActivity, SessionStatus
from app.services.ai_service import AIService
from app.services.dynamic_question_service import DynamicQuestionService
from app.conversation_flow import CONVERSATION_FLOW, get_step_config, get_next_step, is_final_step
from app.core.config import settings


class TeachingService:
    """教学服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
        self.dynamic_question_service = DynamicQuestionService()

    def start_conversation(self, user_id: int, use_dynamic_mode: bool = True) -> Dict[str, Any]:
        """
        开始新的教学设计对话

        Args:
            user_id: 用户ID
            use_dynamic_mode: 是否使用动态问题生成模式

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
                current_step=CONVERSATION_FLOW['start_step'] if not use_dynamic_mode else 'dynamic_question_1',
                collected_data={},
                history=[],
                ai_questions_asked=0,
                max_ai_questions=5
            )

            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

            # 获取第一个问题
            if use_dynamic_mode:
                # 使用动态问题生成
                first_question = self._get_dynamic_first_question()
            else:
                # 使用传统固定流程
                first_question = self._get_question_card(CONVERSATION_FLOW['start_step'])

            return {
                "session_id": session_id,
                "question_card": first_question,
                "is_dynamic_mode": use_dynamic_mode
            }

        except Exception as e:
            self.db.rollback()
            print(f"开始对话失败: {type(e).__name__}: {e}")
            print(f"详细错误信息: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="开始对话失败，请稍后重试"
            )

    async def process_answer(self, session_id: str, answer: str) -> Dict[str, Any]:
        """
        处理用户回答并返回下一步问题或最终教案
        
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

            # 根据模式处理回答
            if session.current_step.startswith('dynamic_question_'):
                return await self._process_dynamic_answer(session, answer)
            else:
                return await self._process_traditional_answer(session, answer)

        except Exception as e:
            self.db.rollback()
            print(f"处理回答失败: {type(e).__name__}: {e}")
            print(f"详细错误信息: {traceback.format_exc()}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="处理回答失败，请稍后重试"
            )

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
        删除指定的教案

        Args:
            plan_id: 教案ID
            user_id: 用户ID

        Returns:
            删除是否成功
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
            return False

    def _extract_subject_from_collected_data(self, collected_data: Dict[str, Any]) -> str:
        """
        从收集的数据中智能提取学科信息

        Args:
            collected_data: 收集的用户数据

        Returns:
            学科名称
        """
        # 首先检查直接的subject字段
        if collected_data.get("subject"):
            return collected_data["subject"]

    def _extract_subject_from_collected_data(self, collected_data: Dict[str, Any]) -> str:
        """
        从收集的数据中智能提取学科信息

        Args:
            collected_data: 收集的用户数据

        Returns:
            学科名称
        """
        # 首先检查直接的subject字段
        if collected_data.get("subject"):
            return collected_data["subject"]

        # 优先检查第一个问题的答案（通常直接询问学科）
        first_answer = collected_data.get("question_1_answer", "")
        if first_answer:
            # 直接匹配学科名称
            direct_subjects = {
                "语文": ["语文", "国语", "汉语", "文学"],
                "数学": ["数学", "算术", "代数", "几何"],
                "英语": ["英语", "英文", "English"],
                "物理": ["物理", "物理学"],
                "化学": ["化学", "化学科"],
                "生物": ["生物", "生物学"],
                "历史": ["历史", "历史课"],
                "地理": ["地理", "地理学"],
                "政治": ["政治", "思想政治", "政治课"],
                "音乐": ["音乐", "音乐课"],
                "美术": ["美术", "美术课", "绘画"],
                "体育": ["体育", "体育课", "体操"],
                "信息技术": ["信息技术", "计算机", "编程", "信息科技"],
                "科学": ["科学", "自然科学"],
                "道德与法治": ["道德与法治", "品德", "法治"],
                "劳动": ["劳动", "劳动技术"],
                "综合实践": ["综合实践", "实践活动"],
                # 编程语言单独处理
                "Java": ["Java", "JAVA", "java"],
                "Python": ["Python", "PYTHON", "python"],
                "C++": ["C++", "CPP", "cpp", "c++"],
                "C语言": ["C语言", "C语言编程"],
                "JavaScript": ["JavaScript", "JS", "javascript", "js"],
                "数据结构与算法": ["数据结构", "算法", "数据结构与算法"]
            }

            first_answer_lower = first_answer.lower()
            for subject, keywords in direct_subjects.items():
                if any(keyword.lower() in first_answer_lower for keyword in keywords):
                    return subject

            # 如果第一个答案没有直接匹配，则尝试关键词匹配
            subject_keywords = {
                "数学": ["数学", "算术", "代数", "几何", "微积分", "统计", "计算", "方程"],
                "语文": ["语文", "中文", "文学", "作文", "阅读", "古诗", "诗歌", "散文", "写作"],
                "英语": ["英语", "English", "英文", "单词", "语法", "听力", "口语", "写作", "外语"],
                "物理": ["物理", "力学", "电学", "光学", "热学", "声学", "运动", "能量", "电磁"],
                "化学": ["化学", "元素", "分子", "化合物", "反应", "实验", "原子", "离子", "有机"],
                "生物": ["生物", "细胞", "遗传", "进化", "生态", "植物", "动物", "基因", "微生物"],
                "历史": ["历史", "古代", "近代", "现代", "朝代", "战争", "文明", "文化", "考古"],
                "地理": ["地理", "地图", "气候", "地形", "国家", "城市", "河流", "山脉", "环境"],
                "政治": ["政治", "法律", "宪法", "政府", "公民", "权利", "民主", "法制", "社会"],
                "音乐": ["音乐", "歌曲", "乐器", "节拍", "音符", "合唱", "旋律", "节奏", "乐理"],
                "美术": ["美术", "绘画", "素描", "色彩", "艺术", "创作", "设计", "雕塑", "美学"],
                "体育": ["体育", "运动", "健身", "球类", "跑步", "游泳", "锻炼", "比赛", "体能"],
                "信息技术": ["计算机", "编程", "软件", "网络", "信息技术", "IT", "代码", "程序", "数据库"]
            }

            for subject, keywords in subject_keywords.items():
                if any(keyword in first_answer_lower for keyword in keywords):
                    return subject

        # 如果第一个问题没有匹配，检查其他问题的答案
        for key, value in collected_data.items():
            if key.startswith("question_") and key.endswith("_answer") and value and key != "question_1_answer":
                value_lower = value.lower()
                # 同样使用直接匹配和关键词匹配的逻辑
                for subject, keywords in direct_subjects.items():
                    if any(keyword.lower() in value_lower for keyword in keywords):
                        return subject

                for subject, keywords in subject_keywords.items():
                    if any(keyword in value_lower for keyword in keywords):
                        return subject

        return ""

    def _extract_grade_from_collected_data(self, collected_data: Dict[str, Any]) -> str:
        """
        从收集的数据中智能提取年级信息

        Args:
            collected_data: 收集的用户数据

        Returns:
            年级信息
        """
        # 首先检查直接的grade字段
        if collected_data.get("grade"):
            return collected_data["grade"]

        # 从动态问题答案中提取年级信息
        for key, value in collected_data.items():
            if key.startswith("question_") and key.endswith("_answer") and value:
                # 年级匹配模式 - 按照优先级排序，更具体的匹配在前
                grade_patterns = [
                    # 初中 - 具体年级
                    ("初中一年级", "初中一年级"), ("初中二年级", "初中二年级"), ("初中三年级", "初中三年级"),
                    ("初一", "初中一年级"), ("初二", "初中二年级"), ("初三", "初中三年级"),
                    ("七年级", "初中一年级"), ("八年级", "初中二年级"), ("九年级", "初中三年级"),
                    # 高中 - 具体年级
                    ("高中一年级", "高中一年级"), ("高中二年级", "高中二年级"), ("高中三年级", "高中三年级"),
                    ("高一", "高中一年级"), ("高二", "高中二年级"), ("高三", "高中三年级"),
                    # 小学 - 具体年级
                    ("小学一年级", "小学一年级"), ("小学二年级", "小学二年级"), ("小学三年级", "小学三年级"),
                    ("小学四年级", "小学四年级"), ("小学五年级", "小学五年级"), ("小学六年级", "小学六年级"),
                    # 大学 - 具体年级
                    ("大学一年级", "大学一年级"), ("大学二年级", "大学二年级"), ("大学三年级", "大学三年级"), ("大学四年级", "大学四年级"),
                    ("大一", "大学一年级"), ("大二", "大学二年级"), ("大三", "大学三年级"), ("大四", "大学四年级"),
                    # 研究生
                    ("研究生一年级", "研究生一年级"), ("研究生二年级", "研究生二年级"), ("研究生三年级", "研究生三年级"),
                    ("硕士一年级", "研究生一年级"), ("硕士二年级", "研究生二年级"), ("硕士三年级", "研究生三年级"),
                    ("博士一年级", "博士一年级"), ("博士二年级", "博士二年级"), ("博士三年级", "博士三年级"),
                    # 通用年级（只有在没有学段前缀时才匹配）
                    ("一年级", "小学一年级"), ("二年级", "小学二年级"), ("三年级", "小学三年级"),
                    ("四年级", "小学四年级"), ("五年级", "小学五年级"), ("六年级", "小学六年级"),
                    # 学段（最后匹配）
                    ("初中", "初中"), ("高中", "高中"), ("小学", "小学"), ("大学", "大学"), ("研究生", "研究生"),
                    # 成人教育和职业培训
                    ("成人", "成人"), ("成人教育", "成人"), ("职业培训", "成人"),
                    # 学历层次
                    ("本科生", "大学"), ("本科", "大学"), ("专科生", "大学"), ("专科", "大学"),
                    ("硕士研究生", "研究生"), ("博士研究生", "博士"),
                    # 学习阶段描述
                    ("初学", "入门"), ("入门", "入门"), ("基础", "入门"), ("初级", "入门"),
                    ("中级", "中级"), ("高级", "高级"), ("专业", "高级"),
                    # 幼儿园
                    ("幼儿园", "幼儿园"), ("学前班", "学前班"), ("托儿所", "幼儿园")
                ]

                value_lower = value.lower()
                for pattern, grade in grade_patterns:
                    if pattern in value_lower:
                        return grade

        return ""

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
            # 智能提取学科和年级信息
            subject = self._extract_subject_from_collected_data(collected_data)
            grade = self._extract_grade_from_collected_data(collected_data)
            
            # 创建教案
            lesson_plan = LessonPlan(
                user_id=user_id,
                title=lesson_plan_data['title'],
                subject=subject,
                grade=grade,
                teaching_objective='\n'.join(lesson_plan_data['learning_objectives']),
                teaching_outline=lesson_plan_data['teaching_outline'],
                web_search_info=lesson_plan_data.get('web_search_info')
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

    def _format_lesson_plan_response(self, lesson_plan: LessonPlan, web_search_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        格式化教案响应

        Args:
            lesson_plan: LessonPlan对象
            web_search_info: 联网搜索信息（如果未提供，从数据库中读取）

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

        response = {
            "id": lesson_plan.id,
            "title": lesson_plan.title,
            "subject": lesson_plan.subject,
            "grade": lesson_plan.grade,
            "teaching_objective": lesson_plan.teaching_objective,
            "teaching_outline": lesson_plan.teaching_outline,
            "activities": sorted(activities, key=lambda x: x['order_index']),
            "created_at": lesson_plan.created_at.isoformat() if lesson_plan.created_at else None
        }

        # 使用提供的web_search_info，或者从数据库中读取
        search_info = web_search_info or lesson_plan.web_search_info
        if search_info:
            response["web_search_info"] = search_info

        return response

    def _get_dynamic_first_question(self) -> Dict[str, Any]:
        """
        获取动态模式的第一个问题
        
        Returns:
            第一个问题卡片
        """
        # 第一个问题通常是基础信息收集
        return {
            "step_key": "dynamic_question_1",
            "question": "您好！我们来一起设计一堂精彩的课程。首先，请告诉我这堂课是关于哪个学科的？",
            "question_type": "basic_info",
            "key_to_save": "subject",
            "options": ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理"],
            "allows_free_text": True,
            "priority": "high"
        }
    
    async def _process_dynamic_answer(self, session: LessonCreationSession, answer: str) -> Dict[str, Any]:
        """
        处理动态模式下的用户回答
        
        Args:
            session: 会话对象
            answer: 用户回答
            
        Returns:
            处理结果
        """
        # 记录对话历史
        current_question = self._get_current_question_for_history(session)
        session.history.append({
            "step": session.current_step,
            "question": current_question,
            "answer": answer,
            "question_count": session.ai_questions_asked + 1
        })
        flag_modified(session, "history")
        
        # 保存用户回答 - 使用动态键名
        key_to_save = f"question_{session.ai_questions_asked + 1}_answer"
        session.collected_data[key_to_save] = answer
        
        # 更新问题计数
        session.ai_questions_asked += 1
        flag_modified(session, "collected_data")
        
        # 判断是否应该继续提问
        continue_decision = self.dynamic_question_service.should_continue_questioning(
                session.collected_data,
                session.ai_questions_asked,
                3,  # 使用固定的最小问题数量
                session.max_ai_questions
            )
        
        if not continue_decision["should_continue"]:
            # 结束提问，生成教案
            return await self._finalize_lesson_plan(session)
        
        # 生成下一个问题
        next_question = await self.dynamic_question_service.generate_next_question(
                session.collected_data,
                session.ai_questions_asked,
                session.max_ai_questions
            )
        
        if next_question:
            # 更新会话状态
            session.current_step = f"dynamic_question_{session.ai_questions_asked + 1}"
            self.db.commit()
            
            return {
                "session_id": session.session_id,
                "status": "in_progress",
                "is_dynamic_mode": True,
                "question_card": next_question,
                "question_count": session.ai_questions_asked,
                "max_questions": session.max_ai_questions
            }
        else:
            # 无法生成更多问题，结束流程
            return await self._finalize_lesson_plan(session)
    
    async def _process_traditional_answer(self, session: LessonCreationSession, answer: str) -> Dict[str, Any]:
        """
        处理传统模式下的用户回答
        
        Args:
            session: 会话对象
            answer: 用户回答
            
        Returns:
            处理结果
        """
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
            return await self._finalize_lesson_plan(session)
        else:
            # 更新当前步骤
            session.current_step = next_step
            self.db.commit()

            # 返回下一个问题
            next_question = self._get_question_card(next_step)
            return {
                "session_id": session.session_id,
                "status": "in_progress",
                "is_dynamic_mode": False,
                "question_card": next_question
            }
    
    async def _finalize_lesson_plan(self, session: LessonCreationSession) -> Dict[str, Any]:
        """
        完成教案生成流程
        
        Args:
            session: 会话对象
            
        Returns:
            最终结果
        """
        session.status = SessionStatus.processing
        self.db.commit()

        # 调用AI服务生成教案
        lesson_plan_data = await self.ai_service.generate_lesson_plan(session.collected_data, enable_web_search=True)

        if lesson_plan_data:
            # 保存教案到数据库
            lesson_plan = self._save_lesson_plan(session.user_id, session.collected_data, lesson_plan_data)
            session.lesson_plan_id = lesson_plan.id
            session.status = SessionStatus.completed
            self.db.commit()

            return {
                "session_id": session.session_id,
                "status": "completed",
                "is_dynamic_mode": session.current_step.startswith('dynamic_question_'),
                "lesson_plan": self._format_lesson_plan_response(lesson_plan, lesson_plan_data.get("web_search_info"))
            }
        else:
            session.status = SessionStatus.failed
            self.db.commit()
            raise ValueError("教案生成失败")
    
    def _get_current_question_for_history(self, session: LessonCreationSession) -> str:
        """
        获取当前问题文本用于历史记录
        
        Args:
            session: 会话对象
            
        Returns:
            问题文本
        """
        if session.current_step.startswith('dynamic_question_'):
            # 从历史记录中获取最后一个问题，或返回默认问题
            if session.history:
                return session.history[-1].get("question", "动态生成的问题")
            return "您好！我们来一起设计一堂精彩的课程。"
        else:
            question_card = self._get_question_card(session.current_step)
            return question_card['question']

    def get_active_sessions(self, user_id: int):
        """
        获取用户的活跃会话列表
        
        Args:
            user_id: 用户ID
            
        Returns:
            活跃会话列表
        """
        sessions = self.db.query(LessonCreationSession).filter(
            LessonCreationSession.user_id == user_id,
            LessonCreationSession.status.in_([SessionStatus.IN_PROGRESS, SessionStatus.WAITING_FOR_INPUT])
        ).order_by(LessonCreationSession.created_at.desc()).all()
        
        result = []
        for session in sessions:
            result.append({
                "session_id": session.id,
                "status": session.status.value,
                "is_dynamic_mode": session.current_step.startswith('dynamic_question_'),
                "question_count": session.ai_questions_asked,
                "max_questions": session.max_ai_questions,
                "current_step": session.current_step,
                "collected_data": session.collected_data,
                "created_at": session.created_at
            })
        
        return result

    def get_session_info(self, session_id: str, user_id: int):
        """
        获取会话详情
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            会话详情或None
        """
        session = self.db.query(LessonCreationSession).filter_by(
            id=session_id, user_id=user_id
        ).first()
        
        if not session:
            return None
            
        return {
            "session_id": session.id,
            "status": session.status.value,
            "is_dynamic_mode": session.current_step.startswith('dynamic_question_'),
            "question_count": session.ai_questions_asked,
                "max_questions": session.max_ai_questions,
            "current_step": session.current_step,
            "collected_data": session.collected_data,
            "created_at": session.created_at
        }

    def delete_session(self, session_id: str, user_id: int):
        """
        删除会话
        
        Args:
            session_id: 会话ID
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        session = self.db.query(LessonCreationSession).filter_by(
            id=session_id, user_id=user_id
        ).first()
        
        if not session:
            return False
            
        self.db.delete(session)
        self.db.commit()
        return True