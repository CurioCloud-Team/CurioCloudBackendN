"""
API测试示例

使用httpx库测试认证API的基本功能
"""
import asyncio
import httpx
import json


async def test_api():
    """测试API功能"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # 测试健康检查
        print("🔍 测试健康检查...")
        response = await client.get(f"{base_url}/health")
        print(f"Health Check Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # 测试认证服务健康检查
        print("🔍 测试认证服务健康检查...")
        response = await client.get(f"{base_url}/api/auth/health")
        print(f"Auth Health Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print()
        
        # 测试用户注册
        print("📝 测试用户注册...")
        register_data = {
            "username": "testuser123",
            "email": "test123@example.com",
            "password": "Test123!@#",
            "confirm_password": "Test123!@#",
            "full_name": "测试用户"
        }
        
        response = await client.post(
            f"{base_url}/api/auth/register",
            json=register_data
        )
        
        print(f"Register Status: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"用户ID: {result['user']['id']}")
            print(f"用户名: {result['user']['username']}")
            print(f"邮箱: {result['user']['email']}")
            print(f"令牌类型: {result['token']['token_type']}")
            print(f"消息: {result['message']}")
            access_token = result['token']['access_token']
            print(f"访问令牌: {access_token[:20]}...")
        else:
            print(f"注册失败: {response.text}")
        print()
        
        # 测试用户登录
        print("🔐 测试用户登录...")
        login_data = {
            "username": "testuser123",
            "password": "Test123!@#"
        }
        
        response = await client.post(
            f"{base_url}/api/auth/login",
            json=login_data
        )
        
        print(f"Login Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"用户ID: {result['user']['id']}")
            print(f"用户名: {result['user']['username']}")
            print(f"邮箱: {result['user']['email']}")
            print(f"令牌类型: {result['token']['token_type']}")
            print(f"消息: {result['message']}")
            access_token = result['token']['access_token']
            print(f"访问令牌: {access_token[:20]}...")
        else:
            print(f"登录失败: {response.text}")
        print()
        
        # 测试错误情况 - 重复注册
        print("❌ 测试重复注册错误...")
        response = await client.post(
            f"{base_url}/api/auth/register",
            json=register_data
        )
        print(f"Duplicate Register Status: {response.status_code}")
        if response.status_code != 201:
            error = response.json()
            print(f"错误信息: {error.get('detail', 'Unknown error')}")
        print()
        
        # 测试错误情况 - 错误密码登录
        print("❌ 测试错误密码登录...")
        wrong_login_data = {
            "username": "testuser123",
            "password": "WrongPassword123!"
        }
        
        response = await client.post(
            f"{base_url}/api/auth/login",
            json=wrong_login_data
        )
        print(f"Wrong Password Status: {response.status_code}")
        if response.status_code != 200:
            error = response.json()
            print(f"错误信息: {error.get('detail', 'Unknown error')}")


if __name__ == "__main__":
    print("🚀 开始API测试...")
    print("请确保应用正在运行在 http://localhost:8000")
    print("=" * 50)
    
    try:
        asyncio.run(test_api())
        print("✅ 测试完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("请检查：")
        print("1. 应用是否正在运行")
        print("2. 数据库连接是否正常")
        print("3. 端口8000是否可用")