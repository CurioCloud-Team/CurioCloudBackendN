"""
数据模型测试

测试用户模型和数据验证
"""
import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserLogin, UserResponse
from app.models.user import User


class TestUserSchemas:
    """用户数据模式测试"""
    
    def test_valid_user_create(self):
        """测试有效的用户创建数据"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test123!@#",
            "confirm_password": "Test123!@#",
            "full_name": "测试用户"
        }
        
        user = UserCreate(**user_data)
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.password == "Test123!@#"
        assert user.full_name == "测试用户"
    
    def test_invalid_username(self):
        """测试无效用户名"""
        user_data = {
            "username": "te",  # 太短
            "email": "test@example.com",
            "password": "Test123!@#",
            "confirm_password": "Test123!@#"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_invalid_email(self):
        """测试无效邮箱"""
        user_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "Test123!@#",
            "confirm_password": "Test123!@#"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_weak_password(self):
        """测试弱密码"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "123456",  # 弱密码
            "confirm_password": "123456"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_password_mismatch(self):
        """测试密码不匹配"""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "Test123!@#",
            "confirm_password": "Different123!@#"
        }
        
        with pytest.raises(ValidationError):
            UserCreate(**user_data)
    
    def test_valid_user_login(self):
        """测试有效的登录数据"""
        login_data = {
            "username": "testuser",
            "password": "Test123!@#"
        }
        
        login = UserLogin(**login_data)
        assert login.username == "testuser"
        assert login.password == "Test123!@#"
    
    def test_user_response_schema(self):
        """测试用户响应模式"""
        response_data = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "测试用户",
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        response = UserResponse(**response_data)
        assert response.id == 1
        assert response.username == "testuser"
        assert response.email == "test@example.com"
        assert response.is_active is True
        assert response.is_verified is False


class TestUserModel:
    """用户模型测试"""
    
    def test_user_model_creation(self):
        """测试用户模型创建"""
        user = User(
            username="testuser",
            email="test@example.com",
            full_name="测试用户",
            hashed_password="hashed_password_here",
            is_active=True,  # 显式设置，因为在非数据库上下文中默认值不会自动应用
            is_verified=False
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.full_name == "测试用户"
        assert user.hashed_password == "hashed_password_here"
        assert user.is_active is True
        assert user.is_verified is False
    
    def test_user_model_repr(self):
        """测试用户模型字符串表示"""
        user = User(
            id=1,
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password"
        )
        
        repr_str = repr(user)
        assert "User(id=1" in repr_str
        assert "username='testuser'" in repr_str
        assert "email='test@example.com'" in repr_str