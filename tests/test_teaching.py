"""
教学模块测试

测试对话式教学设计功能
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.services.teaching_service import TeachingService
from app.models import SessionStatus
from app.conversation_flow import CONVERSATION_FLOW


class TestTeachingService:
    """教学服务测试类"""

    def test_start_conversation(self, client, authenticated_user):
        """测试开始对话"""
        # 使用API测试而不是直接调用服务
        response = client.post(
            "/api/teaching/conversational/start",
            headers=authenticated_user["headers"]
        )

        assert response.status_code == 201
        data = response.json()
        assert "session_id" in data
        assert "question_card" in data
        assert data["question_card"]["step_key"] == CONVERSATION_FLOW['start_step']

    def test_process_answer_subject(self, client, authenticated_user):
        """测试处理学科回答"""
        # 开始对话
        start_response = client.post(
            "/api/teaching/conversational/start",
            headers=authenticated_user["headers"]
        )
        assert start_response.status_code == 201
        session_id = start_response.json()["session_id"]

        # 提交学科回答
        response = client.post(
            "/api/teaching/conversational/next",
            json={"session_id": session_id, "answer": "生物"},
            headers=authenticated_user["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert "question_card" in data
        assert data["question_card"]["step_key"] == "ask_grade"

    def test_get_lesson_plans_empty(self, client, authenticated_user):
        """测试获取空教案列表"""
        response = client.get(
            "/api/teaching/lesson-plans",
            headers=authenticated_user["headers"]
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_conversation_flow_config(self):
        """测试对话流程配置"""
        from app.conversation_flow import get_step_config, get_next_step, is_final_step

        # 测试获取步骤配置
        subject_config = get_step_config('ask_subject')
        assert subject_config is not None
        assert subject_config['key_to_save'] == 'subject'

        # 测试获取下一步
        next_step = get_next_step('ask_subject')
        assert next_step == 'ask_grade'

        # 测试是否为最终步骤
        assert not is_final_step('ask_subject')
        assert is_final_step('ask_duration')  # 因为下一步是'finalize'


class TestAIService:
    """AI服务测试类"""

    @pytest.mark.asyncio
    @patch('app.services.ai_service.httpx.AsyncClient')
    async def test_generate_lesson_plan_success(self, mock_client):
        """测试AI生成教案成功"""
        from app.services.ai_service import AIService

        # 模拟成功的API响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"title": "测试教案", "learning_objectives": ["目标1"], "teaching_outline": "大纲", "activities": []}'
                }
            }]
        }

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        service = AIService()
        result = await service.generate_lesson_plan({
            "subject": "生物",
            "grade": "初中二年级",
            "topic": "光合作用",
            "duration_minutes": 45
        })

        assert result is not None
        assert result["title"] == "测试教案"

    @pytest.mark.asyncio
    @patch('app.services.ai_service.httpx.AsyncClient')
    async def test_generate_lesson_plan_failure(self, mock_client):
        """测试AI生成教案失败"""
        from app.services.ai_service import AIService

        # 模拟失败的API响应
        mock_response = Mock()
        mock_response.status_code = 500

        mock_client.return_value.__aenter__.return_value.post = AsyncMock(return_value=mock_response)

        service = AIService()
        result = await service.generate_lesson_plan({
            "subject": "生物",
            "grade": "初中二年级",
            "topic": "光合作用",
            "duration_minutes": 45
        })

        assert result is None