"""
Celery 异步任务配置
"""
from celery import Celery
from app.core.config import settings

# 创建 Celery 实例
celery_app = Celery(
    "ai_tuning",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.training_tasks"]
)

# Celery 配置
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600 * 12,  # 12 小时超时
    worker_prefetch_multiplier=1,  # 防止内存占用过高
    task_acks_late=True,
    worker_max_tasks_per_child=1,  # 防止内存泄漏
)

# 任务路由配置
celery_app.conf.task_routes = {
    "app.tasks.training_tasks.*": {"queue": "training"},
}
