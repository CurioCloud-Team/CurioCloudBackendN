"""
完整功能测试

测试全新用户的注册和登录流程
"""
import asyncio
import httpx
import json
import random
import string


def generate_random_user():
    """生成随机用户数据"""
    random_id = ''.join(random.choices(string.digits, k=6))
    return {
        "username": f"user{random_id}",
        "email": f"user{random_id}@example.com",
        "password": "Test123!@#",
        "confirm_password": "Test123!@#",
        "full_name": f"测试用户{random_id}"
    }


async def test_complete_flow():
    """测试完整的用户流程"""
    base_url = "http://localhost:8000"
    user_data = generate_random_user()
    
    async with httpx.AsyncClient() as client:
        print(f"🆕 测试新用户注册: {user_data['username']}")
        response = await client.post(f"{base_url}/api/auth/register", json=user_data)
        
        print(f"注册状态: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"✅ 注册成功!")
            print(f"   用户ID: {result['user']['id']}")
            print(f"   用户名: {result['user']['username']}")
            print(f"   邮箱: {result['user']['email']}")
            print(f"   全名: {result['user']['full_name']}")
            print(f"   账户状态: {'激活' if result['user']['is_active'] else '未激活'}")
            print(f"   邮箱验证: {'已验证' if result['user']['is_verified'] else '未验证'}")
            print(f"   令牌类型: {result['token']['token_type']}")
            print(f"   令牌过期时间: {result['token']['expires_in']}秒")
            print(f"   消息: {result['message']}")
            
            # 保存令牌用于后续测试
            access_token = result['token']['access_token']
            print(f"   访问令牌: {access_token[:30]}...")
        else:
            print(f"❌ 注册失败: {response.text}")
            return
        
        print()
        print(f"🔐 测试用户登录: {user_data['username']}")
        login_data = {
            "username": user_data['username'],
            "password": user_data['password']
        }
        
        response = await client.post(f"{base_url}/api/auth/login", json=login_data)
        print(f"登录状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 登录成功!")
            print(f"   用户ID: {result['user']['id']}")
            print(f"   用户名: {result['user']['username']}")
            print(f"   消息: {result['message']}")
            print(f"   新令牌: {result['token']['access_token'][:30]}...")
        else:
            print(f"❌ 登录失败: {response.text}")
        
        print()
        print(f"📧 测试邮箱登录: {user_data['email']}")
        email_login_data = {
            "username": user_data['email'],  # 使用邮箱登录
            "password": user_data['password']
        }
        
        response = await client.post(f"{base_url}/api/auth/login", json=email_login_data)
        print(f"邮箱登录状态: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 邮箱登录成功!")
            print(f"   用户名: {result['user']['username']}")
            print(f"   消息: {result['message']}")
        else:
            print(f"❌ 邮箱登录失败: {response.text}")


async def test_validation_errors():
    """测试数据验证错误"""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        print("\n🚫 测试各种验证错误...")
        
        # 测试弱密码
        print("1. 测试弱密码...")
        weak_password_data = {
            "username": "weakuser123",
            "email": "weak123@example.com",
            "password": "123456",
            "confirm_password": "123456",
            "full_name": "弱密码用户"
        }
        
        response = await client.post(f"{base_url}/api/auth/register", json=weak_password_data)
        print(f"   状态: {response.status_code}")
        if response.status_code == 422:
            error = response.json()
            print(f"   ✅ 正确拦截弱密码")
            print(f"   错误详情: {error.get('detail', [{}])[0].get('msg', 'Unknown error')}")
        
        # 测试密码不匹配
        print("2. 测试密码不匹配...")
        mismatch_data = {
            "username": "mismatchuser123",
            "email": "mismatch123@example.com",
            "password": "Test123!@#",
            "confirm_password": "Different123!@#",
            "full_name": "密码不匹配用户"
        }
        
        response = await client.post(f"{base_url}/api/auth/register", json=mismatch_data)
        print(f"   状态: {response.status_code}")
        if response.status_code == 422:
            print(f"   ✅ 正确拦截密码不匹配")
        
        # 测试无效邮箱
        print("3. 测试无效邮箱格式...")
        invalid_email_data = {
            "username": "invalidemail123",
            "email": "invalid-email-format",
            "password": "Test123!@#",
            "confirm_password": "Test123!@#",
            "full_name": "无效邮箱用户"
        }
        
        response = await client.post(f"{base_url}/api/auth/register", json=invalid_email_data)
        print(f"   状态: {response.status_code}")
        if response.status_code == 422:
            print(f"   ✅ 正确拦截无效邮箱格式")


if __name__ == "__main__":
    print("🚀 开始完整功能测试...")
    print("=" * 60)
    
    try:
        asyncio.run(test_complete_flow())
        asyncio.run(test_validation_errors())
        print("\n🎉 所有测试完成!")
    except Exception as e:
        print(f"❌ 测试失败: {e}")