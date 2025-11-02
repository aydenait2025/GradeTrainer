"""
训练管理相关 API
"""
import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.db.database import get_db
from app.db import models
from app.schemas.schemas import (
    TrainingJobCreate, TrainingJobResponse, TrainingLogResponse,
    TrainingProgress, SystemStatus
)
from app.tasks.training_tasks import start_training_task
from app.services.training_service import TrainingService
from app.core.config import settings

router = APIRouter()


@router.post("/jobs", response_model=TrainingJobResponse)
async def create_training_job(
    job_data: TrainingJobCreate,
    file_path: str,
    db: Session = Depends(get_db)
):
    """
    创建新的训练任务
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="上传文件不存在")
    
    # 检查模型是否支持
    if job_data.training_params.model_name not in settings.SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的模型。支持的模型: {', '.join(settings.SUPPORTED_MODELS)}"
        )
    
    # 检查并发训练任务数量
    running_jobs = db.query(models.TrainingJob).filter(
        models.TrainingJob.status.in_(["pending", "running"])
    ).count()
    
    if running_jobs >= settings.MAX_CONCURRENT_TRAINING:
        raise HTTPException(
            status_code=429,
            detail=f"并发训练任务数量已达上限 ({settings.MAX_CONCURRENT_TRAINING})"
        )
    
    # 创建训练任务记录
    training_job = models.TrainingJob(
        job_name=job_data.job_name,
        upload_filename=os.path.basename(file_path),
        upload_path=file_path,
        model_name=job_data.training_params.model_name,
        epochs=job_data.training_params.epochs,
        batch_size=job_data.training_params.batch_size,
        learning_rate=job_data.training_params.learning_rate,
        use_fp16=job_data.training_params.use_fp16,
        use_quantization=job_data.training_params.use_quantization,
        lora_r=job_data.training_params.lora_r,
        lora_alpha=job_data.training_params.lora_alpha,
        lora_dropout=job_data.training_params.lora_dropout,
        status="pending"
    )
    
    db.add(training_job)
    db.commit()
    db.refresh(training_job)
    
    # 启动异步训练任务
    task = start_training_task.delay(training_job.id)
    
    # 更新任务记录
    training_job.celery_task_id = task.id
    db.commit()
    
    return training_job


@router.get("/jobs", response_model=List[TrainingJobResponse])
async def get_training_jobs(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取训练任务列表
    """
    query = db.query(models.TrainingJob)
    
    if status:
        query = query.filter(models.TrainingJob.status == status)
    
    jobs = query.order_by(desc(models.TrainingJob.created_at)).offset(skip).limit(limit).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=TrainingJobResponse)
async def get_training_job(job_id: int, db: Session = Depends(get_db)):
    """
    获取特定训练任务详情
    """
    job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    return job


@router.delete("/jobs/{job_id}")
async def delete_training_job(job_id: int, db: Session = Depends(get_db)):
    """
    删除训练任务
    """
    job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    # 如果任务正在运行，先停止
    if job.status in ["pending", "running"] and job.celery_task_id:
        from app.core.celery import celery_app
        celery_app.control.revoke(job.celery_task_id, terminate=True)
    
    # 删除相关文件
    training_service = TrainingService()
    try:
        training_service.cleanup_job_files(job_id)
    except Exception as e:
        # 记录错误但不阻止删除
        print(f"清理文件失败: {e}")
    
    # 删除数据库记录
    db.delete(job)
    db.commit()
    
    return {"message": "训练任务删除成功"}


@router.post("/jobs/{job_id}/stop")
async def stop_training_job(job_id: int, db: Session = Depends(get_db)):
    """
    停止训练任务
    """
    job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    if job.status not in ["pending", "running"]:
        raise HTTPException(status_code=400, detail="任务未在运行中")
    
    if job.celery_task_id:
        from app.core.celery import celery_app
        celery_app.control.revoke(job.celery_task_id, terminate=True)
        
        # 更新状态
        job.status = "stopped"
        db.commit()
        
        return {"message": "训练任务停止成功"}
    else:
        raise HTTPException(status_code=400, detail="无法停止任务")


@router.get("/jobs/{job_id}/logs", response_model=List[TrainingLogResponse])
async def get_training_logs(
    job_id: int,
    skip: int = 0,
    limit: int = 1000,
    log_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取训练日志
    """
    # 检查任务是否存在
    job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    # 查询日志
    query = db.query(models.TrainingLog).filter(models.TrainingLog.job_id == job_id)
    
    if log_level:
        query = query.filter(models.TrainingLog.log_level == log_level)
    
    logs = query.order_by(models.TrainingLog.timestamp).offset(skip).limit(limit).all()
    return logs


@router.get("/jobs/{job_id}/progress", response_model=TrainingProgress)
async def get_training_progress(job_id: int, db: Session = Depends(get_db)):
    """
    获取训练进度
    """
    job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    # 从最新的日志中获取进度信息
    latest_log = db.query(models.TrainingLog).filter(
        models.TrainingLog.job_id == job_id,
        models.TrainingLog.metrics.isnot(None)
    ).order_by(desc(models.TrainingLog.timestamp)).first()
    
    if not latest_log or not latest_log.metrics:
        # 返回默认进度
        return TrainingProgress(
            job_id=job_id,
            current_epoch=0,
            total_epochs=job.epochs,
            current_step=0,
            total_steps=0
        )
    
    metrics = latest_log.metrics
    return TrainingProgress(
        job_id=job_id,
        current_epoch=metrics.get("epoch", 0),
        total_epochs=job.epochs,
        current_step=metrics.get("step", 0),
        total_steps=metrics.get("total_steps", 0),
        current_loss=metrics.get("loss"),
        average_loss=metrics.get("avg_loss"),
        learning_rate=metrics.get("lr"),
        elapsed_time=metrics.get("elapsed_time"),
        estimated_remaining=metrics.get("eta")
    )


@router.get("/status", response_model=SystemStatus)
async def get_system_status(db: Session = Depends(get_db)):
    """
    获取系统状态
    """
    # 统计任务数量
    total_jobs = db.query(models.TrainingJob).count()
    running_jobs = db.query(models.TrainingJob).filter(
        models.TrainingJob.status.in_(["pending", "running"])
    ).count()
    completed_jobs = db.query(models.TrainingJob).filter(
        models.TrainingJob.status == "completed"
    ).count()
    failed_jobs = db.query(models.TrainingJob).filter(
        models.TrainingJob.status == "failed"
    ).count()
    
    # 获取系统资源信息
    training_service = TrainingService()
    gpu_usage = training_service.get_gpu_usage()
    disk_usage = training_service.get_disk_usage()
    memory_usage = training_service.get_memory_usage()
    
    return SystemStatus(
        total_jobs=total_jobs,
        running_jobs=running_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        gpu_usage=gpu_usage,
        disk_usage=disk_usage,
        memory_usage=memory_usage
    )


@router.post("/jobs/{job_id}/restart")
async def restart_training_job(job_id: int, db: Session = Depends(get_db)):
    """
    重启失败的训练任务
    """
    job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="训练任务不存在")
    
    if job.status not in ["failed", "stopped"]:
        raise HTTPException(status_code=400, detail="只能重启失败或停止的任务")
    
    # 检查并发限制
    running_jobs = db.query(models.TrainingJob).filter(
        models.TrainingJob.status.in_(["pending", "running"])
    ).count()
    
    if running_jobs >= settings.MAX_CONCURRENT_TRAINING:
        raise HTTPException(
            status_code=429,
            detail=f"并发训练任务数量已达上限 ({settings.MAX_CONCURRENT_TRAINING})"
        )
    
    # 重置任务状态
    job.status = "pending"
    job.celery_task_id = None
    job.started_at = None
    job.completed_at = None
    
    # 启动新的训练任务
    task = start_training_task.delay(job.id)
    job.celery_task_id = task.id
    
    db.commit()
    
    return {"message": "训练任务重启成功"}
