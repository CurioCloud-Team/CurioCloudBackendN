"""
认证API测试

测试用户注册和登录相关的API接口
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthCheck:
    """健康检查测试"""
    
    def test_app_health_check(self, client: TestClient):
        """测试应用健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["message"] == "服务运行正常"
        assert "version" in data
    
    def test_auth_health_check(self, client: TestClient):
        """测试认证服务健康检查"""
        response = client.get("/api/auth/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "认证服务运行正常"
        assert data["success"] is True


class TestUserRegistration:
    """用户注册测试"""
    
    def test_successful_registration(self, client: TestClient, sample_user_data):
        """测试成功注册"""
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["message"] == "注册成功"
        
        # 验证用户信息
        user = data["user"]
        assert user["username"] == sample_user_data["username"]
        assert user["email"] == sample_user_data["email"]
        assert user["full_name"] == sample_user_data["full_name"]
        assert user["is_active"] is True
        assert user["is_verified"] is False
        assert "id" in user
        
        # 验证令牌信息
        token = data["token"]
        assert token["token_type"] == "bearer"
        assert "access_token" in token
        assert "expires_in" in token
    
    def test_duplicate_username_registration(self, client: TestClient, sample_user_data):
        """测试重复用户名注册"""
        # 第一次注册
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # 第二次注册相同用户名
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "用户名已存在" in data["detail"]
    
    def test_duplicate_email_registration(self, client: TestClient, sample_user_data):
        """测试重复邮箱注册"""
        # 第一次注册
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # 第二次注册相同邮箱但不同用户名
        duplicate_email_data = sample_user_data.copy()
        duplicate_email_data["username"] = "different_user"
        
        response = client.post("/api/auth/register", json=duplicate_email_data)
        assert response.status_code == 400
        
        data = response.json()
        assert "邮箱" in data["detail"] or "用户信息冲突" in data["detail"]
    
    def test_weak_password_registration(self, client: TestClient, sample_user_data):
        """测试弱密码注册"""
        weak_password_data = sample_user_data.copy()
        weak_password_data.update({
            "username": "weakuser",
            "email": "weak@example.com",
            "password": "123456",
            "confirm_password": "123456"
        })
        
        response = client.post("/api/auth/register", json=weak_password_data)
        assert response.status_code == 422
    
    def test_password_without_special_chars_registration(self, client: TestClient, sample_user_data):
        """测试无特殊字符密码注册（新规则下应该成功）"""
        no_special_chars_data = sample_user_data.copy()
        no_special_chars_data.update({
            "username": "nospecialuser",
            "email": "nospecial@example.com",
            "password": "Test12345",  # 包含字母和数字，但无特殊字符
            "confirm_password": "Test12345"
        })
        
        response = client.post("/api/auth/register", json=no_special_chars_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["message"] == "注册成功"
    
    def test_password_mismatch_registration(self, client: TestClient, sample_user_data):
        """测试密码不匹配注册"""
        mismatch_data = sample_user_data.copy()
        mismatch_data.update({
            "username": "mismatchuser",
            "email": "mismatch@example.com",
            "password": "Test123!@#",
            "confirm_password": "Different123!@#"
        })
        
        response = client.post("/api/auth/register", json=mismatch_data)
        assert response.status_code == 422
    
    def test_invalid_email_registration(self, client: TestClient, sample_user_data):
        """测试无效邮箱格式注册"""
        invalid_email_data = sample_user_data.copy()
        invalid_email_data.update({
            "username": "invalidemail",
            "email": "invalid-email-format"
        })
        
        response = client.post("/api/auth/register", json=invalid_email_data)
        assert response.status_code == 422


class TestUserLogin:
    """用户登录测试"""
    
    def test_successful_login_with_username(self, client: TestClient, sample_user_data, sample_login_data):
        """测试用户名登录成功"""
        # 先注册用户
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # 使用用户名登录
        response = client.post("/api/auth/login", json=sample_login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["message"] == "登录成功"
        
        # 验证用户信息
        user = data["user"]
        assert user["username"] == sample_user_data["username"]
        assert user["email"] == sample_user_data["email"]
    
    def test_successful_login_with_email(self, client: TestClient, sample_user_data):
        """测试邮箱登录成功"""
        # 先注册用户
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # 使用邮箱登录
        email_login_data = {
            "username": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        
        response = client.post("/api/auth/login", json=email_login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "登录成功"
        assert data["user"]["email"] == sample_user_data["email"]
    
    def test_login_with_wrong_password(self, client: TestClient, sample_user_data):
        """测试错误密码登录"""
        # 先注册用户
        response = client.post("/api/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        # 使用错误密码登录
        wrong_login_data = {
            "username": sample_user_data["username"],
            "password": "WrongPassword123!"
        }
        
        response = client.post("/api/auth/login", json=wrong_login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "用户名、邮箱或密码错误" in data["detail"]
    
    def test_login_with_nonexistent_user(self, client: TestClient):
        """测试不存在的用户登录"""
        login_data = {
            "username": "nonexistent",
            "password": "Test123!@#"
        }
        
        response = client.post("/api/auth/login", json=login_data)
        assert response.status_code == 401
        
        data = response.json()
        assert "用户名、邮箱或密码错误" in data["detail"]


class TestRootEndpoint:
    """根路径测试"""
    
    def test_root_endpoint(self, client: TestClient):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "运行中"