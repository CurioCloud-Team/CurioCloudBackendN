"""
简化的API测试

专门测试重复注册功能
"""
import asyncio
import httpx
import json


async def test_duplicate_registration():
    """测试重复注册功能"""
    base_url = "http://localhost:8000"
    
    register_data = {
        "username": "duplicate_test_user",
        "email": "duplicate@example.com",
        "password": "Test123!@#",
        "confirm_password": "Test123!@#",
        "full_name": "重复测试用户"
    }
    
    async with httpx.AsyncClient() as client:
        print("📝 第一次注册...")
        response = await client.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"第一次注册状态: {response.status_code}")
        if response.status_code == 201:
            result = response.json()
            print(f"✅ 注册成功: {result['user']['username']}")
        else:
            print(f"❌ 注册失败: {response.text}")
        print()
        
        print("📝 第二次注册（应该失败）...")
        response = await client.post(f"{base_url}/api/auth/register", json=register_data)
        print(f"第二次注册状态: {response.status_code}")
        if response.status_code != 201:
            error = response.json()
            print(f"✅ 正确处理重复注册: {error.get('detail', 'Unknown error')}")
        else:
            print("❌ 重复注册应该失败但却成功了")


if __name__ == "__main__":
    print("🚀 测试重复注册处理...")
    print("=" * 40)
    
    try:
        asyncio.run(test_duplicate_registration())
        print("\n✅ 测试完成")
    except Exception as e:
        print(f"❌ 测试失败: {e}")