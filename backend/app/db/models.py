"""
数据库模型定义
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class TrainingJob(Base):
    """训练任务模型"""
    __tablename__ = "training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String, nullable=False, index=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    
    # 文件信息
    upload_filename = Column(String, nullable=False)
    upload_path = Column(String, nullable=False)
    data_path = Column(String)  # 解析后的数据路径
    
    # 训练参数
    model_name = Column(String, nullable=False)
    epochs = Column(Integer, default=3)
    batch_size = Column(Integer, default=4)
    learning_rate = Column(Float, default=2e-4)
    use_fp16 = Column(Boolean, default=True)
    use_quantization = Column(Boolean, default=False)
    lora_r = Column(Integer, default=16)
    lora_alpha = Column(Integer, default=32)
    lora_dropout = Column(Float, default=0.1)
    
    # 训练结果
    final_loss = Column(Float)
    validation_accuracy = Column(Float)
    model_path = Column(String)  # 微调后模型路径
    
    # Celery 任务 ID
    celery_task_id = Column(String, index=True)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 关联日志
    logs = relationship("TrainingLog", back_populates="job")


class TrainingLog(Base):
    """训练日志模型"""
    __tablename__ = "training_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("training_jobs.id"), nullable=False)
    
    # 日志内容
    log_level = Column(String, default="INFO")  # INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    
    # 训练指标 (JSON 格式)
    metrics = Column(JSON)  # {"epoch": 1, "loss": 0.5, "accuracy": 0.8}
    
    # 时间戳
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联任务
    job = relationship("TrainingJob", back_populates="logs")


class ModelInfo(Base):
    """模型信息模型"""
    __tablename__ = "model_info"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("training_jobs.id"), nullable=False)
    
    # 模型基本信息
    model_name = Column(String, nullable=False)
    model_path = Column(String, nullable=False)
    model_size = Column(Float)  # MB
    
    # 模型配置
    config = Column(JSON)
    
    # 部署状态
    is_deployed = Column(Boolean, default=False)
    api_endpoint = Column(String)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DatasetInfo(Base):
    """数据集信息模型"""
    __tablename__ = "dataset_info"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("training_jobs.id"), nullable=False)
    
    # 数据集统计
    total_samples = Column(Integer)
    train_samples = Column(Integer)
    val_samples = Column(Integer)
    test_samples = Column(Integer)
    
    # 数据质量
    avg_input_length = Column(Float)
    avg_output_length = Column(Float)
    unique_labels = Column(Integer)
    
    # 数据集路径
    processed_data_path = Column(String)
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
