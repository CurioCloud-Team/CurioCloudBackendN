"""
认证服务单元测试

测试认证服务的业务逻辑
"""
import pytest
from unittest.mock import Mock, patch
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.services.auth_service import AuthService
from app.schemas.user import UserCreate
from app.models.user import User


class TestAuthService:
    """认证服务测试"""
    
    @pytest.fixture
    def mock_db(self):
        """模拟数据库会话"""
        return Mock()
    
    @pytest.fixture
    def auth_service(self, mock_db):
        """创建认证服务实例"""
        return AuthService(mock_db)
    
    @pytest.fixture
    def user_create_data(self):
        """用户创建数据"""
        return UserCreate(
            username="testuser",
            email="test@example.com",
            password="Test123!@#",
            confirm_password="Test123!@#",
            full_name="测试用户"
        )
    
    def test_register_user_success(self, auth_service, mock_db, user_create_data):
        """测试用户注册成功"""
        from datetime import datetime
        
        # 模拟查询结果 - 用户不存在
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # 模拟创建的用户
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = "testuser"
        mock_user.email = "test@example.com"
        mock_user.full_name = "测试用户"
        mock_user.is_active = True
        mock_user.is_verified = False
        mock_user.created_at = datetime.now()
        mock_user.updated_at = datetime.now()
        
        mock_db.refresh.return_value = None
        mock_db.add.return_value = None
        mock_db.commit.return_value = None
        
        # 配置refresh后的用户对象
        def mock_refresh(user):
            user.id = 1
            user.username = "testuser"
            user.email = "test@example.com"
            user.full_name = "测试用户"
            user.is_active = True
            user.is_verified = False
            user.created_at = datetime.now()
            user.updated_at = datetime.now()
        
        mock_db.refresh.side_effect = mock_refresh
        
        with patch('app.services.auth_service.hash_password') as mock_hash, \
             patch('app.services.auth_service.create_access_token') as mock_token, \
             patch('app.services.auth_service.get_token_expire_time') as mock_expire:
            
            mock_hash.return_value = "hashed_password"
            mock_token.return_value = "test_token"
            mock_expire.return_value = 1800
            
            result = auth_service.register_user(user_create_data)
            
            assert result.message == "注册成功"
            assert result.token.access_token == "test_token"
            assert result.token.expires_in == 1800
            
            # 验证数据库操作
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    def test_register_user_duplicate_username(self, auth_service, mock_db, user_create_data):
        """测试重复用户名注册"""
        # 模拟查询结果 - 用户名已存在
        existing_user = Mock()
        existing_user.username = "testuser"
        existing_user.email = "other@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(user_create_data)
        
        assert exc_info.value.status_code == 400
        assert "用户名已存在" in exc_info.value.detail
    
    def test_register_user_duplicate_email(self, auth_service, mock_db, user_create_data):
        """测试重复邮箱注册"""
        # 模拟查询结果 - 邮箱已存在
        existing_user = Mock()
        existing_user.username = "otheruser"
        existing_user.email = "test@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user
        
        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(user_create_data)
        
        assert exc_info.value.status_code == 400
        assert "邮箱已被注册" in exc_info.value.detail


class TestPasswordSecurity:
    """密码安全测试"""
    
    def test_password_hashing(self):
        """测试密码哈希"""
        from app.utils.security import hash_password, verify_password
        
        password = "Test123!@#"
        hashed = hash_password(password)
        
        assert hashed != password
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False


class TestJWTToken:
    """JWT令牌测试"""
    
    def test_create_and_verify_token(self):
        """测试JWT令牌创建和验证"""
        from app.utils.jwt import create_access_token, verify_token
        
        test_data = {"sub": "testuser", "user_id": 1}
        token = create_access_token(test_data)
        
        assert token is not None
        assert isinstance(token, str)
        
        # 验证令牌
        token_data = verify_token(token)
        assert token_data is not None
        assert token_data.username == "testuser"
        assert token_data.user_id == 1
    
    def test_verify_invalid_token(self):
        """测试无效令牌验证"""
        from app.utils.jwt import verify_token
        
        invalid_token = "invalid.token.here"
        token_data = verify_token(invalid_token)
        
        assert token_data is None