"""
测试配置

提供测试用的数据库和应用配置
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.core.config import settings
from main import app

# 创建测试数据库引擎（使用内存数据库）
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """覆盖数据库依赖用于测试"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def client():
    """创建测试客户端"""
    # 创建测试数据库表
    Base.metadata.create_all(bind=engine)
    
    # 覆盖数据库依赖
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # 清理
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "Test123!@#",
        "confirm_password": "Test123!@#",
        "full_name": "测试用户"
    }


@pytest.fixture
def sample_login_data():
    """示例登录数据"""
    return {
        "username": "testuser",
        "password": "Test123!@#"
    }


@pytest.fixture
def auth_headers(client: TestClient, sample_user_data):
    """获取认证头部"""
    # 注册用户
    register_response = client.post("/api/auth/register", json=sample_user_data)
    assert register_response.status_code == 201  # 注册接口返回201
    
    # 获取令牌
    token = register_response.json()["token"]["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def authenticated_user(client: TestClient, sample_user_data):
    """创建已认证的用户并返回用户信息和令牌"""
    # 注册用户
    register_response = client.post("/api/auth/register", json=sample_user_data)
    assert register_response.status_code == 201  # 注册接口返回201
    
    response_data = register_response.json()
    
    return {
        "user": response_data["user"],
        "token": response_data["token"]["access_token"],
        "headers": {"Authorization": f"Bearer {response_data['token']['access_token']}"}
    }