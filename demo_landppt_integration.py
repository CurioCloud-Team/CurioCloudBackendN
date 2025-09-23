#!/usr/bin/env python3
"""
CurioCloud Backend - LandPPT集成演示脚本

演示如何使用API将教案转换为PPT
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# 配置
BASE_URL = "http://localhost:8000"  # CurioCloud Backend URL
LANDPPT_URL = "http://localhost:8001"  # LandPPT URL

# 示例用户认证令牌（需要先登录获取）
# AUTH_TOKEN = "your_jwt_token_here"
AUTH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0IiwidXNlcl9pZCI6NCwiZXhwIjoxNzY0NjM5OTg5fQ.7_SQd8U37GZtpLzl9aY4gX9ApihsBA5ZGsY8-B_1CiM"

async def demo_lesson_plan_to_ppt():
    """演示教案到PPT的完整流程"""

    print("=== CurioCloud Backend - LandPPT集成演示 ===\n")

    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {
            "Authorization": f"Bearer {AUTH_TOKEN}",
            "Content-Type": "application/json"
        }

        try:
            # 步骤1: 获取用户的教案列表
            print("1. 获取教案列表...")
            response = await client.get(
                f"{BASE_URL}/api/teaching/lesson-plans",
                headers=headers
            )

            if response.status_code == 200:
                lesson_plans = response.json()
                print(f"✅ 找到 {len(lesson_plans)} 个教案")

                if lesson_plans:
                    # 选择第一个教案进行演示
                    lesson_plan = lesson_plans[0]
                    plan_id = lesson_plan['id']
                    print(f"📋 选择教案: {lesson_plan['title']} (ID: {plan_id})")
                else:
                    print("❌ 没有找到教案，请先创建一个教案")
                    return
            else:
                print(f"❌ 获取教案列表失败: {response.status_code}")
                print(response.text)
                return

            # 步骤2: 从教案生成PPT
            print(f"\n2. 从教案 {plan_id} 生成PPT...")
            response = await client.post(
                f"{BASE_URL}/api/teaching/lesson-plans/{plan_id}/generate-ppt",
                headers=headers
            )

            if response.status_code == 201:
                ppt_result = response.json()
                ppt_project_id = ppt_result['ppt_project_id']
                print("✅ PPT生成任务已启动")
                print(f"   项目ID: {ppt_project_id}")
                print(f"   标题: {ppt_result['ppt_title']}")
                print(f"   场景: {ppt_result['ppt_scenario']}")
            else:
                print(f"❌ PPT生成失败: {response.status_code}")
                print(response.text)
                return

            # 步骤3: 查询PPT生成状态
            print(f"\n3. 查询PPT生成状态...")
            max_attempts = 10
            for attempt in range(max_attempts):
                response = await client.get(
                    f"{BASE_URL}/api/teaching/ppt/{ppt_project_id}/status",
                    headers=headers
                )

                if response.status_code == 200:
                    status_info = response.json()
                    status = status_info['status']

                    print(f"   状态: {status['status']}")
                    print(f"   进度: {status['progress']:.1f}%")

                    if status['status'] == 'completed':
                        print(f"   幻灯片数量: {status['slides_count']}")
                        break
                    elif status['status'] == 'failed':
                        print("❌ PPT生成失败")
                        return
                else:
                    print(f"❌ 查询状态失败: {response.status_code}")
                    return

                if attempt < max_attempts - 1:
                    print("   等待5秒后重试...")
                    await asyncio.sleep(5)

            # 步骤4: 获取幻灯片内容
            print("\n4. 获取PPT幻灯片内容...")
            response = await client.get(
                f"{BASE_URL}/api/teaching/ppt/{ppt_project_id}/slides",
                headers=headers
            )

            if response.status_code == 200:
                slides_info = response.json()
                print("✅ 幻灯片内容获取成功")
                print(f"   幻灯片数量: {slides_info['slides_count']}")
                print(f"   HTML内容长度: {len(slides_info.get('slides_html', ''))}")
            else:
                print(f"❌ 获取幻灯片失败: {response.status_code}")

            # 步骤5: 导出PPT文件（演示）
            print("\n5. 导出PPT文件...")
            print("   演示导出PDF格式...")
            print(f"   下载URL: {BASE_URL}/api/teaching/ppt/{ppt_project_id}/export/pdf")
            print("   演示导出PPTX格式...")
            print(f"   下载URL: {BASE_URL}/api/teaching/ppt/{ppt_project_id}/export/pptx")

            print("\n=== 演示完成 ===")
            print("\n📝 使用说明:")
            print(f"1. 确保CurioCloud Backend运行在: {BASE_URL}")
            print(f"2. 确保LandPPT服务运行在: {LANDPPT_URL}")
            print("3. 使用有效的JWT令牌进行API调用")
            print("4. PPT生成需要一些时间，请耐心等待")

        except httpx.RequestError as e:
            print(f"❌ 网络请求错误: {e}")
        except Exception as e:
            print(f"❌ 演示过程中发生错误: {e}")


async def check_services():
    """检查服务状态"""
    print("检查服务状态...\n")

    async with httpx.AsyncClient(timeout=10.0) as client:
        # 检查CurioCloud Backend
        try:
            response = await client.get(f"{BASE_URL}/docs")
            if response.status_code == 200:
                print(f"✅ CurioCloud Backend: {BASE_URL} - 运行中")
            else:
                print(f"❌ CurioCloud Backend: {BASE_URL} - 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ CurioCloud Backend: {BASE_URL} - 连接失败 ({e})")

        # 检查LandPPT
        try:
            response = await client.get(f"{LANDPPT_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ LandPPT: {LANDPPT_URL} - 运行中")
                print(f"   服务: {health_data.get('service', 'unknown')}")
                print(f"   默认AI提供商: {health_data.get('ai_provider', 'unknown')}")
            else:
                print(f"❌ LandPPT: {LANDPPT_URL} - 状态码 {response.status_code}")
        except Exception as e:
            print(f"❌ LandPPT: {LANDPPT_URL} - 连接失败 ({e})")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        # 只检查服务状态
        asyncio.run(check_services())
    else:
        # 运行完整演示
        print("注意：运行完整演示需要有效的JWT令牌")
        print("请先登录获取令牌，然后修改脚本中的 AUTH_TOKEN 变量\n")

        # 先检查服务状态
        asyncio.run(check_services())
        print()

        # 如果有有效的令牌，则运行演示
        if AUTH_TOKEN != "your_jwt_token_here":
            asyncio.run(demo_lesson_plan_to_ppt())
        else:
            print("请设置有效的AUTH_TOKEN后重新运行")
            print("获取令牌方法：")
            print("1. 访问CurioCloud登录页面")
            print("2. 使用API登录端点获取JWT令牌")
            print("3. 将令牌填入脚本的AUTH_TOKEN变量")