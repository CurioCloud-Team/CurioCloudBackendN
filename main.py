"""
CurioCloud Backend 主应用

FastAPI应用程序的入口点，配置和启动整个应用
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import create_tables
from app.routers import auth_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用程序生命周期管理
    
    在应用启动时创建数据库表
    """
    # 启动时的操作
    print("🚀 正在启动 CurioCloud Backend...")
    
    # 创建数据库表
    try:
        create_tables()
        print("✅ 数据库表创建成功")
    except Exception as e:
        print(f"❌ 数据库表创建失败: {e}")
    
    yield
    
    # 关闭时的操作
    print("🛑 CurioCloud Backend 正在关闭...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CurioCloud 后端服务 - 提供用户认证和数据管理功能",
    docs_url="/docs" if settings.debug else None,  # 生产环境隐藏文档
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else ["https://your-frontend-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)


@app.get("/", tags=["根路径"])
async def root():
    """根路径接口 - 返回API基本信息"""
    return {
        "message": f"欢迎使用 {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "文档在生产环境中已隐藏",
        "status": "运行中"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """应用健康检查接口"""
    return {
        "status": "healthy",
        "message": "服务运行正常",
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn
    
    # 开发环境启动配置
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info"
    )
