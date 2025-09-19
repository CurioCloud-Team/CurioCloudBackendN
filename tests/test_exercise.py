"""
练习题模块测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app
from app.models.user import User
from app.models.lesson_plan import LessonPlan
from app.models.exercise import Question
from tests.conftest import auth_headers, test_user_data

client = TestClient(app)

@pytest.fixture(scope="function")
def test_lesson_plan(db: Session, authenticated_user: dict):
    """创建一个测试用的教案"""
    user_info = authenticated_user['user']
    lesson_plan = LessonPlan(
        user_id=user_info['id'],
        title="测试教案：光合作用",
        subject="生物",
        grade="初中二年级",
        teaching_objective="理解光合作用",
        teaching_outline="光合作用的详细过程"
    )
    db.add(lesson_plan)
    db.commit()
    db.refresh(lesson_plan)
    return lesson_plan

def test_generate_multiple_choice_questions(
    client: TestClient,
    db: Session,
    authenticated_user: dict,
    test_lesson_plan: LessonPlan,
    mocker
):
    """测试生成选择题的API"""
    # Mock the AI service call
    mock_response = [
        {
            "content": "植物进行光合作用的主要场所是？",
            "choices": [
                {"content": "叶绿体", "is_correct": True},
                {"content": "线粒体", "is_correct": False},
                {"content": "细胞核", "is_correct": False},
                {"content": "细胞质", "is_correct": False},
            ],
            "answer": "叶绿体是光合作用的场所。"
        }
    ]
    mocker.patch(
        "app.services.ai_service.AIService.generate_multiple_choice_questions",
        return_value=mock_response
    )

    headers = authenticated_user['headers']
    response = client.post(
        f"/api/exercises/lesson-plan/{test_lesson_plan.id}/generate-multiple-choice",
        headers=headers,
        json={"num_questions": 1, "difficulty": "easy"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["content"] == "植物进行光合作用的主要场所是？"
    assert len(data[0]["choices"]) == 4
    assert data[0]["choices"][0]["content"] == "叶绿体"
    assert data[0]["choices"][0]["is_correct"] is True

    # 验证数据库中是否已保存
    question_in_db = db.query(Question).filter(Question.content == "植物进行光合作用的主要场所是？").first()
    assert question_in_db is not None
    assert question_in_db.lesson_plan_id == test_lesson_plan.id
    assert len(question_in_db.choices) == 4


