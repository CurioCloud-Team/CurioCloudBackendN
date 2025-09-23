"""
应用程序配置管理

使用Pydantic Settings从环境变量加载配置
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用程序设置类"""
    
    # 应用程序配置
    app_name: str = "CurioCloud Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 数据库配置
    database_host: str
    database_port: int = 3306
    database_user: str
    database_password: str
    database_name: str
    
    # JWT配置
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # OpenRouter LLM配置
    openrouter_api_key: str
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "google/gemini-2.5-flash"
    llm_max_retries: int = 3
    llm_timeout_seconds: int = 120
    
    # Tavily搜索配置
    tavily_api_key: Optional[str] = None
    tavily_base_url: str = "https://api.tavily.com"
    tavily_search_max_results: int = 5
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def database_url(self) -> str:
        """构建数据库连接URL"""
        return f"mysql+pymysql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"


# 创建全局配置实例
settings = Settings()