"""
系统配置管理
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    # 项目基本信息
    PROJECT_NAME: str = "AI Model Tuning System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://username:password@localhost/ai_tuning_db"
    # 开发环境可使用 SQLite
    # DATABASE_URL: str = "sqlite:///./ai_tuning.db"
    
    # Redis 配置 (用于 Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS 配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React 开发服务器
        "http://localhost:5173",  # Vite 开发服务器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # 文件上传配置
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    UPLOAD_DIR: str = "uploads"
    MODEL_DIR: str = "models"
    
    # AI 训练配置
    SUPPORTED_MODELS: List[str] = [
        "meta-llama/Llama-2-7b-chat-hf",
        "bigcode/starcoderbase-7b",
        "microsoft/DialoGPT-medium"
    ]
    
    # GPU 配置
    CUDA_VISIBLE_DEVICES: str = "0"
    MAX_CONCURRENT_TRAINING: int = 2
    
    # JWT 配置 (如果需要用户认证)
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    class Config:
        env_file = ".env"


settings = Settings()
