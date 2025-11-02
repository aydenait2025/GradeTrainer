"""
Pydantic 数据模式定义
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# 训练参数模式
class TrainingParams(BaseModel):
    """训练参数"""
    model_name: str = Field(..., description="模型名称")
    epochs: int = Field(3, ge=1, le=50, description="训练轮数")
    batch_size: int = Field(4, ge=1, le=32, description="批次大小")
    learning_rate: float = Field(2e-4, gt=0, lt=1, description="学习率")
    use_fp16: bool = Field(True, description="是否使用 FP16")
    use_quantization: bool = Field(False, description="是否使用量化")
    lora_r: int = Field(16, ge=4, le=128, description="LoRA rank")
    lora_alpha: int = Field(32, ge=8, le=256, description="LoRA alpha")
    lora_dropout: float = Field(0.1, ge=0, le=0.5, description="LoRA dropout")


# 训练任务创建请求
class TrainingJobCreate(BaseModel):
    """创建训练任务请求"""
    job_name: str = Field(..., description="任务名称")
    training_params: TrainingParams


# 训练任务响应
class TrainingJobResponse(BaseModel):
    """训练任务响应"""
    id: int
    job_name: str
    status: str
    upload_filename: str
    model_name: str
    epochs: int
    batch_size: int
    learning_rate: float
    use_fp16: bool
    use_quantization: bool
    lora_r: int
    lora_alpha: int
    lora_dropout: float
    final_loss: Optional[float] = None
    validation_accuracy: Optional[float] = None
    model_path: Optional[str] = None
    celery_task_id: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 训练日志
class TrainingLogResponse(BaseModel):
    """训练日志响应"""
    id: int
    job_id: int
    log_level: str
    message: str
    metrics: Optional[Dict[str, Any]] = None
    timestamp: datetime
    
    class Config:
        from_attributes = True


# 模型信息
class ModelInfoResponse(BaseModel):
    """模型信息响应"""
    id: int
    job_id: int
    model_name: str
    model_path: str
    model_size: Optional[float] = None
    config: Optional[Dict[str, Any]] = None
    is_deployed: bool
    api_endpoint: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 数据集信息
class DatasetInfoResponse(BaseModel):
    """数据集信息响应"""
    id: int
    job_id: int
    total_samples: Optional[int] = None
    train_samples: Optional[int] = None
    val_samples: Optional[int] = None
    test_samples: Optional[int] = None
    avg_input_length: Optional[float] = None
    avg_output_length: Optional[float] = None
    unique_labels: Optional[int] = None
    processed_data_path: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# 文件上传响应
class FileUploadResponse(BaseModel):
    """文件上传响应"""
    filename: str
    file_path: str
    file_size: int
    upload_time: datetime
    data_preview: Optional[Dict[str, Any]] = None


# 训练进度
class TrainingProgress(BaseModel):
    """训练进度"""
    job_id: int
    current_epoch: int
    total_epochs: int
    current_step: int
    total_steps: int
    current_loss: Optional[float] = None
    average_loss: Optional[float] = None
    learning_rate: Optional[float] = None
    elapsed_time: Optional[float] = None
    estimated_remaining: Optional[float] = None


# 模型预测请求
class PredictionRequest(BaseModel):
    """模型预测请求"""
    model_id: int
    input_text: str
    max_length: int = Field(512, ge=1, le=2048)
    temperature: float = Field(0.7, ge=0.1, le=2.0)
    top_p: float = Field(0.9, ge=0.1, le=1.0)


# 模型预测响应
class PredictionResponse(BaseModel):
    """模型预测响应"""
    input_text: str
    generated_text: str
    confidence: Optional[float] = None
    processing_time: float


# 系统状态
class SystemStatus(BaseModel):
    """系统状态"""
    total_jobs: int
    running_jobs: int
    completed_jobs: int
    failed_jobs: int
    gpu_usage: Optional[Dict[str, Any]] = None
    disk_usage: Optional[Dict[str, Any]] = None
    memory_usage: Optional[Dict[str, Any]] = None


# 错误响应
class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
