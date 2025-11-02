"""
Celery 训练任务
"""
import os
import json
import traceback
from datetime import datetime
from typing import Dict, Any

from celery import current_task
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.core.celery import celery_app
from app.core.config import settings
from app.db import models
from app.services.data_processor import DataProcessor
from app.training.trainer import ModelTrainer


# 创建数据库会话
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@celery_app.task(bind=True)
def start_training_task(self, job_id: int):
    """
    启动训练任务
    
    Args:
        job_id: 训练任务 ID
    """
    db = SessionLocal()
    
    try:
        # 获取训练任务
        job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
        if not job:
            raise ValueError(f"训练任务 {job_id} 不存在")
        
        # 更新任务状态
        job.status = "running"
        job.started_at = datetime.now()
        db.commit()
        
        # 记录开始日志
        log_info(db, job_id, "开始训练任务")
        
        # 1. 数据处理阶段
        self.update_state(state='PROGRESS', meta={'stage': 'data_processing', 'progress': 0})
        
        log_info(db, job_id, "开始处理数据...")
        processor = DataProcessor()
        
        # 确定文件类型
        file_extension = os.path.splitext(job.upload_filename)[1].lower()
        if file_extension == '.zip':
            file_type = 'zip'
        elif file_extension in ['.csv', '.xlsx']:
            file_type = file_extension[1:]  # 去掉点号
        else:
            raise ValueError(f"不支持的文件类型: {file_extension}")
        
        # 处理上传的数据
        processed_result = processor.process_uploaded_data(job.upload_path, file_type)
        
        # 创建训练数据集
        dataset = processor.create_training_dataset(processed_result['processed_data'])
        
        # 保存数据集信息到数据库
        dataset_info = models.DatasetInfo(
            job_id=job_id,
            total_samples=dataset['statistics']['total_samples'],
            train_samples=len(dataset['train']['texts']),
            val_samples=len(dataset['validation']['texts']),
            test_samples=len(dataset['test']['texts']),
            avg_input_length=dataset['statistics']['text_length_stats']['mean'],
            unique_labels=dataset['statistics']['unique_labels'],
            processed_data_path=processed_result.get('data_path')
        )
        db.add(dataset_info)
        db.commit()
        
        log_info(db, job_id, f"数据处理完成，共 {dataset['statistics']['total_samples']} 个样本")
        
        # 2. 模型训练阶段
        self.update_state(state='PROGRESS', meta={'stage': 'model_training', 'progress': 20})
        
        log_info(db, job_id, "开始模型训练...")
        
        # 创建训练器
        trainer = ModelTrainer(
            model_name=job.model_name,
            output_dir=os.path.join(settings.MODEL_DIR, f"job_{job_id}"),
            job_id=job_id,
            db_session=db
        )
        
        # 配置训练参数
        training_args = {
            "epochs": job.epochs,
            "batch_size": job.batch_size,
            "learning_rate": job.learning_rate,
            "use_fp16": job.use_fp16,
            "use_quantization": job.use_quantization,
            "lora_r": job.lora_r,
            "lora_alpha": job.lora_alpha,
            "lora_dropout": job.lora_dropout
        }
        
        # 开始训练
        training_result = trainer.train(
            dataset=dataset,
            training_args=training_args,
            progress_callback=lambda progress: self.update_state(
                state='PROGRESS',
                meta={
                    'stage': 'model_training',
                    'progress': 20 + int(progress * 0.6)  # 20-80%
                }
            )
        )
        
        # 3. 模型保存和验证阶段
        self.update_state(state='PROGRESS', meta={'stage': 'model_saving', 'progress': 80})
        
        log_info(db, job_id, "保存训练后的模型...")
        
        # 保存模型信息到数据库
        model_info = models.ModelInfo(
            job_id=job_id,
            model_name=job.model_name,
            model_path=training_result['model_path'],
            model_size=training_result.get('model_size'),
            config=training_result.get('config'),
            is_deployed=False
        )
        db.add(model_info)
        
        # 更新训练任务结果
        job.final_loss = training_result.get('final_loss')
        job.validation_accuracy = training_result.get('validation_accuracy')
        job.model_path = training_result['model_path']
        job.status = "completed"
        job.completed_at = datetime.now()
        
        db.commit()
        
        # 4. 完成
        self.update_state(state='SUCCESS', meta={'stage': 'completed', 'progress': 100})
        
        log_info(db, job_id, f"训练完成！最终损失: {training_result.get('final_loss', 'N/A')}")
        
        return {
            'job_id': job_id,
            'status': 'completed',
            'final_loss': training_result.get('final_loss'),
            'validation_accuracy': training_result.get('validation_accuracy'),
            'model_path': training_result['model_path']
        }
        
    except Exception as e:
        # 记录错误
        error_msg = f"训练失败: {str(e)}"
        log_error(db, job_id, error_msg)
        
        # 更新任务状态
        if job:
            job.status = "failed"
            job.completed_at = datetime.now()
            db.commit()
        
        # 更新 Celery 任务状态
        self.update_state(
            state='FAILURE',
            meta={
                'stage': 'failed',
                'error': error_msg,
                'traceback': traceback.format_exc()
            }
        )
        
        raise e
        
    finally:
        db.close()


def log_info(db, job_id: int, message: str, metrics: Dict[str, Any] = None):
    """记录信息日志"""
    log = models.TrainingLog(
        job_id=job_id,
        log_level="INFO",
        message=message,
        metrics=metrics
    )
    db.add(log)
    db.commit()


def log_warning(db, job_id: int, message: str, metrics: Dict[str, Any] = None):
    """记录警告日志"""
    log = models.TrainingLog(
        job_id=job_id,
        log_level="WARNING",
        message=message,
        metrics=metrics
    )
    db.add(log)
    db.commit()


def log_error(db, job_id: int, message: str, metrics: Dict[str, Any] = None):
    """记录错误日志"""
    log = models.TrainingLog(
        job_id=job_id,
        log_level="ERROR",
        message=message,
        metrics=metrics
    )
    db.add(log)
    db.commit()


@celery_app.task
def cleanup_old_files():
    """清理旧文件的定时任务"""
    import shutil
    from datetime import timedelta
    
    cutoff_date = datetime.now() - timedelta(days=7)  # 7天前的文件
    
    # 清理上传目录
    upload_dir = settings.UPLOAD_DIR
    if os.path.exists(upload_dir):
        for item in os.listdir(upload_dir):
            item_path = os.path.join(upload_dir, item)
            try:
                item_stat = os.stat(item_path)
                item_date = datetime.fromtimestamp(item_stat.st_mtime)
                
                if item_date < cutoff_date:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    print(f"清理旧文件: {item_path}")
                    
            except Exception as e:
                print(f"清理文件 {item_path} 时出错: {e}")
    
    return "文件清理完成"


@celery_app.task
def validate_training_environment():
    """验证训练环境的定时任务"""
    from app.services.training_service import TrainingService
    
    training_service = TrainingService()
    result = training_service.validate_training_environment()
    
    # 如果环境有问题，记录日志
    if result["overall_status"] != "ready":
        print(f"训练环境检查: {result['overall_status']}")
        for check_name, check_result in result["checks"].items():
            if check_result["status"] != "ok":
                print(f"  {check_name}: {check_result['message']}")
    
    return result


@celery_app.task
def generate_training_report(job_id: int):
    """生成训练报告"""
    db = SessionLocal()
    
    try:
        # 获取训练任务信息
        job = db.query(models.TrainingJob).filter(models.TrainingJob.id == job_id).first()
        if not job:
            raise ValueError(f"训练任务 {job_id} 不存在")
        
        # 获取相关信息
        dataset_info = db.query(models.DatasetInfo).filter(
            models.DatasetInfo.job_id == job_id
        ).first()
        
        model_info = db.query(models.ModelInfo).filter(
            models.ModelInfo.job_id == job_id
        ).first()
        
        logs = db.query(models.TrainingLog).filter(
            models.TrainingLog.job_id == job_id
        ).all()
        
        # 生成报告
        report = {
            "job_info": {
                "id": job.id,
                "name": job.job_name,
                "status": job.status,
                "model_name": job.model_name,
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "training_duration": str(job.completed_at - job.started_at) if job.completed_at and job.started_at else None
            },
            "training_params": {
                "epochs": job.epochs,
                "batch_size": job.batch_size,
                "learning_rate": job.learning_rate,
                "use_fp16": job.use_fp16,
                "use_quantization": job.use_quantization,
                "lora_r": job.lora_r,
                "lora_alpha": job.lora_alpha,
                "lora_dropout": job.lora_dropout
            },
            "results": {
                "final_loss": job.final_loss,
                "validation_accuracy": job.validation_accuracy
            },
            "dataset_info": {
                "total_samples": dataset_info.total_samples if dataset_info else None,
                "train_samples": dataset_info.train_samples if dataset_info else None,
                "val_samples": dataset_info.val_samples if dataset_info else None,
                "test_samples": dataset_info.test_samples if dataset_info else None,
                "avg_input_length": dataset_info.avg_input_length if dataset_info else None,
                "unique_labels": dataset_info.unique_labels if dataset_info else None
            },
            "model_info": {
                "model_path": model_info.model_path if model_info else None,
                "model_size": model_info.model_size if model_info else None,
                "is_deployed": model_info.is_deployed if model_info else False
            },
            "log_summary": {
                "total_logs": len(logs),
                "info_logs": len([log for log in logs if log.log_level == "INFO"]),
                "warning_logs": len([log for log in logs if log.log_level == "WARNING"]),
                "error_logs": len([log for log in logs if log.log_level == "ERROR"])
            }
        }
        
        # 保存报告
        report_dir = os.path.join(settings.MODEL_DIR, f"job_{job_id}")
        os.makedirs(report_dir, exist_ok=True)
        
        report_path = os.path.join(report_dir, "training_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return {
            "report_path": report_path,
            "report": report
        }
        
    finally:
        db.close()
