"""
用户资料管理API测试

测试用户资料获取和更新相关的API接口
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import json


class TestUserProfile:
    """用户资料测试"""
    
    def test_get_profile_without_auth(self, client: TestClient):
        """测试未认证获取用户资料"""
        response = client.get("/api/user/profile")
        assert response.status_code == 403
    
    def test_get_profile_with_invalid_token(self, client: TestClient):
        """测试使用无效令牌获取用户资料"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/api/user/profile", headers=headers)
        assert response.status_code == 401
        
        data = response.json()
        assert "无法验证用户凭据" in data["detail"]
    
    def test_get_profile_success(self, client: TestClient, auth_headers):
        """测试成功获取用户资料"""
        response = client.get("/api/user/profile", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "full_name" in data
        assert "is_active" in data
        assert "is_verified" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_update_profile_without_auth(self, client: TestClient):
        """测试未认证更新用户资料"""
        update_data = {
            "full_name": "新用户名",
            "email": "newemail@example.com"
        }
        response = client.put("/api/user/profile", json=update_data)
        assert response.status_code == 403
    
    def test_update_profile_with_invalid_token(self, client: TestClient):
        """测试使用无效令牌更新用户资料"""
        headers = {"Authorization": "Bearer invalid_token"}
        update_data = {
            "full_name": "新用户名"
        }
        response = client.put("/api/user/profile", json=update_data, headers=headers)
        assert response.status_code == 401
    
    def test_update_profile_full_name_only(self, client: TestClient, auth_headers):
        """测试只更新用户全名"""
        update_data = {
            "full_name": "更新后的用户名"
        }
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "更新后的用户名"
    
    def test_update_profile_email_only(self, client: TestClient, auth_headers):
        """测试只更新用户邮箱"""
        update_data = {
            "email": "updated@example.com"
        }
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "updated@example.com"
    
    def test_update_profile_both_fields(self, client: TestClient, auth_headers):
        """测试同时更新全名和邮箱"""
        update_data = {
            "full_name": "完整更新的用户名",
            "email": "complete_update@example.com"
        }
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["full_name"] == "完整更新的用户名"
        assert data["email"] == "complete_update@example.com"
    
    def test_update_profile_empty_data(self, client: TestClient, auth_headers):
        """测试使用空数据更新资料"""
        update_data = {}
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 200  # 空更新应该成功，但不改变任何内容
    
    def test_update_profile_invalid_email(self, client: TestClient, auth_headers):
        """测试使用无效邮箱格式更新"""
        update_data = {
            "email": "invalid-email-format"
        }
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 422  # 数据验证失败
    
    def test_update_profile_empty_string_fields(self, client: TestClient, auth_headers):
        """测试使用空字符串更新字段"""
        update_data = {
            "full_name": "",
            "email": ""
        }
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 422  # 验证应该失败
    
    def test_update_profile_duplicate_email(self, client: TestClient, auth_headers):
        """测试使用已被其他用户占用的邮箱更新"""
        # 首先注册另一个用户
        register_data = {
            "username": "anotheruser",
            "email": "another@example.com",
            "password": "AnotherPass123!",
            "confirm_password": "AnotherPass123!",
            "full_name": "另一个用户"
        }
        client.post("/api/auth/register", json=register_data)
        
        # 然后尝试使用这个邮箱更新当前用户
        update_data = {
            "email": "another@example.com"
        }
        response = client.put("/api/user/profile", json=update_data, headers=auth_headers)
        assert response.status_code == 400
        
        data = response.json()
        assert "邮箱已被其他用户使用" in data["detail"]


class TestUserStatus:
    """用户状态测试"""
    
    def test_get_user_status_without_auth(self, client: TestClient):
        """测试未认证获取用户状态"""
        response = client.get("/api/user/profile/status")
        assert response.status_code == 403
    
    def test_get_user_status_success(self, client: TestClient, auth_headers):
        """测试成功获取用户状态"""
        response = client.get("/api/user/profile/status", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "success" in data
        assert data["success"] is True
        assert "账户已激活" in data["message"] or "账户已禁用" in data["message"]
        assert "邮箱已验证" in data["message"] or "邮箱未验证" in data["message"]


class TestUserProfileIntegration:
    """用户资料集成测试"""
    
    def test_complete_profile_workflow(self, client: TestClient):
        """测试完整的用户资料工作流"""
        # 1. 注册用户
        register_data = {
            "username": "workflowuser",
            "email": "workflow@example.com",
            "password": "Workflow123!",
            "confirm_password": "Workflow123!",
            "full_name": "工作流测试用户"
        }
        register_response = client.post("/api/auth/register", json=register_data)
        assert register_response.status_code == 201  # 注册接口返回201
        
        # 获取认证令牌
        token = register_response.json()["token"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. 获取初始资料
        profile_response = client.get("/api/user/profile", headers=headers)
        assert profile_response.status_code == 200
        initial_profile = profile_response.json()
        assert initial_profile["username"] == "workflowuser"
        assert initial_profile["email"] == "workflow@example.com"
        assert initial_profile["full_name"] == "工作流测试用户"
        
        # 3. 更新资料
        update_data = {
            "full_name": "更新后的工作流用户",
            "email": "updated_workflow@example.com"
        }
        update_response = client.put("/api/user/profile", json=update_data, headers=headers)
        assert update_response.status_code == 200
        updated_profile = update_response.json()
        assert updated_profile["full_name"] == "更新后的工作流用户"
        assert updated_profile["email"] == "updated_workflow@example.com"
        
        # 4. 验证更新是否持久化
        final_profile_response = client.get("/api/user/profile", headers=headers)
        assert final_profile_response.status_code == 200
        final_profile = final_profile_response.json()
        assert final_profile["full_name"] == "更新后的工作流用户"
        assert final_profile["email"] == "updated_workflow@example.com"
        
        # 5. 检查用户状态
        status_response = client.get("/api/user/profile/status", headers=headers)
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert "workflowuser" in status_data["message"]