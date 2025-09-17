"""
快速API测试

使用requests库测试API基本功能
"""
import requests
import json

def test_basic_api():
    """测试基本API功能"""
    base_url = "http://127.0.0.1:8000"
    
    try:
        # 测试健康检查
        print("🔍 测试健康检查...")
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health Check Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        print()
        
        # 测试根路径
        print("🏠 测试根路径...")
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"Root Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
        print()
        
        # 测试用户注册
        print("📝 测试用户注册...")
        register_data = {
            "username": "testuser2024",
            "email": "test2024@example.com",
            "password": "Test123!@#",
            "confirm_password": "Test123!@#",
            "full_name": "测试用户2024"
        }
        
        response = requests.post(
            f"{base_url}/api/auth/register",
            json=register_data,
            timeout=10
        )
        
        print(f"Register Status: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"✅ 注册成功!")
            print(f"用户ID: {result['user']['id']}")
            print(f"用户名: {result['user']['username']}")
            print(f"邮箱: {result['user']['email']}")
            print(f"消息: {result['message']}")
            token = result['token']['access_token']
            print(f"访问令牌: {token[:30]}...")
        else:
            print(f"❌ 注册失败: {response.text}")
        print()
        
        # 测试用户登录
        print("🔐 测试用户登录...")
        login_data = {
            "username": "testuser2024",
            "password": "Test123!@#"
        }
        
        response = requests.post(
            f"{base_url}/api/auth/login",
            json=login_data,
            timeout=10
        )
        
        print(f"Login Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功!")
            print(f"用户ID: {result['user']['id']}")
            print(f"用户名: {result['user']['username']}")
            print(f"消息: {result['message']}")
        else:
            print(f"❌ 登录失败: {response.text}")
        
        print("\n🎉 API测试完成!")
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保应用正在运行在 http://127.0.0.1:8000")
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 测试出错: {e}")

if __name__ == "__main__":
    print("🚀 开始快速API测试...")
    print("=" * 50)
    test_basic_api()