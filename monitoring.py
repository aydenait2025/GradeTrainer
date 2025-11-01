"""
监控相关 API
"""
import psutil
import os
from typing import Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.database import get_db
from app.db import models
from app.core.config import settings

router = APIRouter()


@router.get("/system")
async def get_system_metrics():
    """
    获取系统资源监控信息
    """
    # CPU 使用率
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # 内存使用情况
    memory = psutil.virtual_memory()
    
    # 磁盘使用情况
    disk_usage = psutil.disk_usage('/')
    
    # GPU 使用情况（如果有 nvidia-ml-py）
    gpu_info = get_gpu_info()
    
    return {
        "cpu": {
            "usage_percent": cpu_percent,
            "core_count": cpu_count,
            "load_average": os.getloadavg() if hasattr(os, 'getloadavg') else None
        },
        "memory": {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "usage_percent": memory.percent
        },
        "disk": {
            "total": disk_usage.total,
            "used": disk_usage.used,
            "free": disk_usage.free,
            "usage_percent": (disk_usage.used / disk_usage.total) * 100
        },
        "gpu": gpu_info,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/training/statistics")
async def get_training_statistics(db: Session = Depends(get_db)):
    """
    获取训练统计信息
    """
    # 按状态统计任务数量
    status_stats = db.query(
        models.TrainingJob.status,
        func.count(models.TrainingJob.id).label('count')
    ).group_by(models.TrainingJob.status).all()
    
    # 按模型统计
    model_stats = db.query(
        models.TrainingJob.model_name,
        func.count(models.TrainingJob.id).label('count')
    ).group_by(models.TrainingJob.model_name).all()
    
    # 最近 7 天的任务创建趋势
    seven_days_ago = datetime.now() - timedelta(days=7)
    daily_stats = db.query(
        func.date(models.TrainingJob.created_at).label('date'),
        func.count(models.TrainingJob.id).label('count')
    ).filter(
        models.TrainingJob.created_at >= seven_days_ago
    ).group_by(
        func.date(models.TrainingJob.created_at)
    ).all()
    
    # 平均训练时间
    completed_jobs = db.query(models.TrainingJob).filter(
        models.TrainingJob.status == "completed",
        models.TrainingJob.started_at.isnot(None),
        models.TrainingJob.completed_at.isnot(None)
    ).all()
    
    avg_training_time = None
    if completed_jobs:
        total_time = sum([
            (job.completed_at - job.started_at).total_seconds()
            for job in completed_jobs
        ])
        avg_training_time = total_time / len(completed_jobs)
    
    return {
        "status_distribution": {status: count for status, count in status_stats},
        "model_distribution": {model: count for model, count in model_stats},
        "daily_trend": [
            {"date": str(date), "count": count} 
            for date, count in daily_stats
        ],
        "average_training_time_seconds": avg_training_time,
        "total_jobs": db.query(models.TrainingJob).count(),
        "completed_jobs": len(completed_jobs)
    }


@router.get("/training/active")
async def get_active_training_jobs(db: Session = Depends(get_db)):
    """
    获取当前活跃的训练任务
    """
    active_jobs = db.query(models.TrainingJob).filter(
        models.TrainingJob.status.in_(["pending", "running"])
    ).all()
    
    jobs_info = []
    for job in active_jobs:
        # 获取最新的训练进度
        latest_log = db.query(models.TrainingLog).filter(
            models.TrainingLog.job_id == job.id,
            models.TrainingLog.metrics.isnot(None)
        ).order_by(models.TrainingLog.timestamp.desc()).first()
        
        progress = {}
        if latest_log and latest_log.metrics:
            progress = latest_log.metrics
        
        jobs_info.append({
            "job_id": job.id,
            "job_name": job.job_name,
            "status": job.status,
            "model_name": job.model_name,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "current_epoch": progress.get("epoch", 0),
            "total_epochs": job.epochs,
            "current_loss": progress.get("loss"),
            "celery_task_id": job.celery_task_id
        })
    
    return {
        "active_jobs": jobs_info,
        "total_active": len(active_jobs)
    }


@router.get("/celery/status")
async def get_celery_status():
    """
    获取 Celery 队列状态
    """
    try:
        from app.core.celery import celery_app
        
        # 获取活跃任务
        active_tasks = celery_app.control.inspect().active()
        
        # 获取预定任务
        scheduled_tasks = celery_app.control.inspect().scheduled()
        
        # 获取保留任务
        reserved_tasks = celery_app.control.inspect().reserved()
        
        # 统计信息
        stats = celery_app.control.inspect().stats()
        
        return {
            "active_tasks": active_tasks,
            "scheduled_tasks": scheduled_tasks,
            "reserved_tasks": reserved_tasks,
            "worker_stats": stats,
            "available_workers": list(stats.keys()) if stats else []
        }
        
    except Exception as e:
        return {
            "error": f"无法连接到 Celery: {str(e)}",
            "active_tasks": {},
            "scheduled_tasks": {},
            "reserved_tasks": {},
            "worker_stats": {},
            "available_workers": []
        }


@router.get("/logs/recent")
async def get_recent_logs(
    limit: int = 100,
    log_level: str = None,
    job_id: int = None,
    db: Session = Depends(get_db)
):
    """
    获取最近的训练日志
    """
    query = db.query(models.TrainingLog)
    
    if job_id:
        query = query.filter(models.TrainingLog.job_id == job_id)
    
    if log_level:
        query = query.filter(models.TrainingLog.log_level == log_level)
    
    logs = query.order_by(
        models.TrainingLog.timestamp.desc()
    ).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": log.id,
                "job_id": log.job_id,
                "log_level": log.log_level,
                "message": log.message,
                "metrics": log.metrics,
                "timestamp": log.timestamp.isoformat()
            }
            for log in logs
        ],
        "total_count": len(logs)
    }


@router.get("/storage/usage")
async def get_storage_usage():
    """
    获取存储使用情况
    """
    upload_dir = settings.UPLOAD_DIR
    model_dir = settings.MODEL_DIR
    
    def get_directory_size(path):
        """计算目录大小"""
        if not os.path.exists(path):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total_size += os.path.getsize(filepath)
                except (OSError, IOError):
                    pass
        return total_size
    
    upload_size = get_directory_size(upload_dir)
    model_size = get_directory_size(model_dir)
    
    # 磁盘总使用情况
    disk_usage = psutil.disk_usage('/')
    
    return {
        "upload_directory": {
            "path": upload_dir,
            "size_bytes": upload_size,
            "size_mb": upload_size / (1024 * 1024)
        },
        "model_directory": {
            "path": model_dir,
            "size_bytes": model_size,
            "size_mb": model_size / (1024 * 1024)
        },
        "total_used": {
            "size_bytes": upload_size + model_size,
            "size_mb": (upload_size + model_size) / (1024 * 1024)
        },
        "disk_usage": {
            "total_bytes": disk_usage.total,
            "used_bytes": disk_usage.used,
            "free_bytes": disk_usage.free,
            "usage_percent": (disk_usage.used / disk_usage.total) * 100
        }
    }


def get_gpu_info() -> Dict[str, Any]:
    """获取 GPU 信息"""
    try:
        import pynvml
        pynvml.nvmlInit()
        
        device_count = pynvml.nvmlDeviceGetCount()
        gpus = []
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            
            # 基本信息
            name = pynvml.nvmlDeviceGetName(handle).decode()
            
            # 内存使用情况
            mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            
            # GPU 使用率
            util = pynvml.nvmlDeviceGetUtilizationRates(handle)
            
            # 温度
            try:
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            except:
                temp = None
            
            gpus.append({
                "index": i,
                "name": name,
                "memory": {
                    "total": mem_info.total,
                    "used": mem_info.used,
                    "free": mem_info.free,
                    "usage_percent": (mem_info.used / mem_info.total) * 100
                },
                "utilization": {
                    "gpu_percent": util.gpu,
                    "memory_percent": util.memory
                },
                "temperature": temp
            })
        
        return {
            "available": True,
            "device_count": device_count,
            "devices": gpus
        }
        
    except ImportError:
        return {
            "available": False,
            "error": "pynvml not installed"
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e)
        }


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    系统健康检查
    """
    checks = {}
    overall_status = "healthy"
    
    # 数据库连接检查
    try:
        db.execute("SELECT 1")
        checks["database"] = {"status": "healthy", "message": "连接正常"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "unhealthy"
    
    # Celery 连接检查
    try:
        from app.core.celery import celery_app
        stats = celery_app.control.inspect().stats()
        if stats:
            checks["celery"] = {"status": "healthy", "message": "连接正常", "workers": len(stats)}
        else:
            checks["celery"] = {"status": "unhealthy", "message": "无可用 worker"}
            overall_status = "degraded"
    except Exception as e:
        checks["celery"] = {"status": "unhealthy", "message": str(e)}
        overall_status = "unhealthy"
    
    # 存储空间检查
    disk_usage = psutil.disk_usage('/')
    disk_percent = (disk_usage.used / disk_usage.total) * 100
    
    if disk_percent > 90:
        checks["storage"] = {"status": "unhealthy", "message": f"磁盘使用率过高: {disk_percent:.1f}%"}
        overall_status = "unhealthy"
    elif disk_percent > 80:
        checks["storage"] = {"status": "degraded", "message": f"磁盘使用率较高: {disk_percent:.1f}%"}
        if overall_status == "healthy":
            overall_status = "degraded"
    else:
        checks["storage"] = {"status": "healthy", "message": f"磁盘使用率正常: {disk_percent:.1f}%"}
    
    # GPU 检查
    gpu_info = get_gpu_info()
    if gpu_info["available"]:
        checks["gpu"] = {"status": "healthy", "message": f"发现 {gpu_info['device_count']} 个 GPU 设备"}
    else:
        checks["gpu"] = {"status": "degraded", "message": "未检测到 GPU 或驱动问题"}
        if overall_status == "healthy":
            overall_status = "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "checks": checks
    }
