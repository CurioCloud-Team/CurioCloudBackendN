"""
测试配置

提供测试用的数据库和应用配置
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
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


@pytest.fixture(scope="function")
def db():
    """数据库会话fixture"""
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def client(db):
    """创建测试客户端"""
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
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
def auth_headers(client: TestClient, test_user_data):
    """获取认证头部"""
    # 注册用户
    register_response = client.post("/api/auth/register", json=test_user_data)
    assert register_response.status_code == 201  # 注册接口返回201
    
    # 获取令牌
    token = register_response.json()["token"]["access_token"]
    
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def authenticated_user(client: TestClient, test_user_data, db: Session):
    """创建已认证的用户并返回用户信息和令牌"""
    from app.models.user import User
    from app.services.auth_service import AuthService

    # 确保用户在数据库中
    user = db.query(User).filter(User.username == test_user_data["username"]).first()
    if not user:
        auth_service = AuthService(db)
        user = auth_service.register_user(
            username=test_user_data["username"],
            email=test_user_data["email"],
            password=test_user_data["password"],
            full_name=test_user_data["full_name"]
        )
    
    # 登录获取token
    login_response = client.post("/api/auth/login", data={
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    })
    assert login_response.status_code == 200
    
    token_data = login_response.json()["token"]
    
    # 从数据库获取最新的用户信息
    db.refresh(user)

    return {
        "user": user,
        "token": token_data["access_token"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"}
    }