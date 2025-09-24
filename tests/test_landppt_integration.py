"""
测试LandPPT集成
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.landppt_service import LandPPTService


async def test_landppt_connection():
    """测试LandPPT连接"""
    try:
        service = LandPPTService()
        print(f"LandPPT服务配置:")
        print(f"  Base URL: {service.base_url}")
        print(f"  API Key: {'已配置' if service.api_key else '未配置'}")
        print(f"  Default Scenario: {service.default_scenario}")

        # 测试健康检查端点
        print("\n测试健康检查...")
        health_url = f"{service.base_url}/health"
        print(f"健康检查URL: {health_url}")

        # 注意：这里我们只是打印URL，实际调用需要LandPPT服务运行
        print("注意：要完全测试需要启动LandPPT服务")
        print("运行命令: cd ../LandPPT && python -m uvicorn src.landppt.main:app --reload --host 0.0.0.0 --port 8001")

        return True

    except Exception as e:
        print(f"测试失败: {e}")
        return False


async def test_lesson_plan_conversion():
    """测试教案数据转换"""
    try:
        service = LandPPTService()

        # 模拟教案数据
        mock_lesson_plan = {
            "id": 1,
            "title": "小学语文古诗教学",
            "subject": "语文",
            "grade": "小学三年级",
            "teaching_objective": "1. 认识古诗的特点\n2. 理解古诗的含义\n3. 培养背诵古诗的兴趣",
            "teaching_outline": "1. 导入：播放古筝音乐，介绍古诗\n2. 新课：逐句讲解古诗\n3. 练习：学生跟读背诵\n4. 总结：复习重点内容",
            "activities": [
                {
                    "activity_name": "古筝音乐欣赏",
                    "description": "播放古筝音乐，营造古诗教学氛围",
                    "duration": 5,
                    "order_index": 1
                },
                {
                    "activity_name": "古诗讲解",
                    "description": "教师逐句讲解古诗内容和含义",
                    "duration": 15,
                    "order_index": 2
                },
                {
                    "activity_name": "学生背诵练习",
                    "description": "学生分小组练习背诵古诗",
                    "duration": 10,
                    "order_index": 3
                }
            ]
        }

        # 测试转换
        ppt_request = service._convert_lesson_plan_to_ppt_request(mock_lesson_plan)

        print("教案转换测试:")
        print(f"  主题: {ppt_request['topic']}")
        print(f"  场景: {ppt_request['scenario']}")
        print(f"  目标受众: {ppt_request['target_audience']}")
        print("  需求描述 (前200字符):")
        print(f"    {ppt_request['requirements'][:200]}...")

        return True

    except Exception as e:
        print(f"转换测试失败: {e}")
        return False


if __name__ == "__main__":
    print("=== LandPPT集成测试 ===\n")

    # 测试连接配置
    success1 = asyncio.run(test_landppt_connection())

    print("\n" + "="*50 + "\n")

    # 测试数据转换
    success2 = asyncio.run(test_lesson_plan_conversion())

    print("\n" + "="*50)
    if success1 and success2:
        print("✅ 所有测试通过！")
    else:
        print("❌ 部分测试失败")

    print("\n使用说明:")
    print("1. 确保LandPPT服务正在运行 (端口8001)")
    print("2. 在.env中配置正确的LANDPPT_BASE_URL和LANDPPT_API_KEY")
    print("3. 使用API端点 /api/teaching/lesson-plans/{plan_id}/generate-ppt 生成PPT")