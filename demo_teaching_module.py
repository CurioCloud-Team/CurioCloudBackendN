"""
对话式教学设计模块演示

展示新实现的对话式教学设计功能
"""
import asyncio
from app.services.ai_service import AIService
from app.conversation_flow import CONVERSATION_FLOW, get_step_config, get_next_step


async def demo_ai_service():
    """演示AI服务功能"""
    print("=== AI服务演示 ===")

    # 注意：这需要有效的OpenRouter API密钥
    # 这里只是展示代码结构，实际运行需要配置.env文件
    ai_service = AIService()

    test_data = {
        "subject": "生物",
        "grade": "初中二年级",
        "topic": "光合作用",
        "duration_minutes": 45
    }

    print(f"测试数据: {test_data}")
    print("注意：实际调用需要有效的API密钥")
    print("AI服务初始化成功 ✓")


def demo_conversation_flow():
    """演示对话流程配置"""
    print("\n=== 对话流程演示 ===")

    print(f"起始步骤: {CONVERSATION_FLOW['start_step']}")

    current_step = CONVERSATION_FLOW['start_step']
    step_count = 1

    while current_step != 'finalize':
        config = get_step_config(current_step)
        print(f"\n步骤 {step_count}: {current_step}")
        print(f"  问题: {config['question']}")
        print(f"  选项: {config['options']}")
        print(f"  允许自由输入: {config['allows_free_text']}")
        print(f"  保存键: {config['key_to_save']}")

        current_step = get_next_step(current_step)
        step_count += 1

    print(f"\n最终步骤: {current_step} (流程结束)")


def demo_database_models():
    """演示数据库模型"""
    print("\n=== 数据库模型演示 ===")

    from app.models import LessonCreationSession, LessonPlan, LessonPlanActivity, SessionStatus

    print("可用模型:")
    print("- LessonCreationSession: 教学会话")
    print("- LessonPlan: 教学计划")
    print("- LessonPlanActivity: 教学活动")
    print(f"- SessionStatus枚举: {[status.value for status in SessionStatus]}")


def demo_api_endpoints():
    """演示API端点"""
    print("\n=== API端点演示 ===")

    endpoints = [
        "POST /api/teaching/conversational/start - 开始新对话",
        "POST /api/teaching/conversational/next - 提交回答",
        "GET /api/teaching/lesson-plans - 获取教案列表",
        "GET /api/teaching/lesson-plans/{id} - 获取单个教案",
        "DELETE /api/teaching/lesson-plans/{id} - 删除教案"
    ]

    for endpoint in endpoints:
        print(f"- {endpoint}")


def main():
    """主演示函数"""
    print("🎓 CurioCloud 对话式教学设计模块演示")
    print("=" * 50)

    # 演示对话流程
    demo_conversation_flow()

    # 演示数据库模型
    demo_database_models()

    # 演示API端点
    demo_api_endpoints()

    # 演示AI服务（异步）
    asyncio.run(demo_ai_service())

    print("\n" + "=" * 50)
    print("✅ 模块演示完成！")
    print("\n📝 使用说明:")
    print("1. 确保.env文件包含有效的OpenRouter API配置")
    print("2. 运行 'python main.py' 启动服务器")
    print("3. 访问 http://localhost:8000/docs 查看API文档")
    print("4. 使用认证后的用户测试对话功能")


if __name__ == "__main__":
    main()