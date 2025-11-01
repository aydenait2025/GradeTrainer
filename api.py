"""
主要 API 路由
"""
from fastapi import APIRouter
from app.api.api_v1.endpoints import upload, training, models, monitoring

api_router = APIRouter()

# 注册各个模块的路由
api_router.include_router(upload.router, prefix="/upload", tags=["文件上传"])
api_router.include_router(training.router, prefix="/training", tags=["训练管理"])
api_router.include_router(models.router, prefix="/models", tags=["模型管理"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["监控"])
