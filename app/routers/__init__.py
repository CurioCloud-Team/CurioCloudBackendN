# API路由包
from .auth import router as auth_router
from .exercise import router as exercise_router

__all__ = ["auth_router", "exercise_router"]