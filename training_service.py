"""
训练服务
"""
import os
import json
import psutil
import shutil
from typing import Dict, Any, Optional
from datetime import datetime


class TrainingService:
    """训练服务"""
    
    def __init__(self):
        pass
    
    def get_gpu_usage(self) -> Optional[Dict[str, Any]]:
        """获取 GPU 使用情况"""
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
    
    def get_disk_usage(self) -> Dict[str, Any]:
        """获取磁盘使用情况"""
        usage = psutil.disk_usage('/')
        
        return {
            "total": usage.total,
            "used": usage.used,
            "free": usage.free,
            "usage_percent": (usage.used / usage.total) * 100
        }
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        memory = psutil.virtual_memory()
        
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "usage_percent": memory.percent,
            "cached": getattr(memory, 'cached', 0),
            "buffers": getattr(memory, 'buffers', 0)
        }
    
    def cleanup_job_files(self, job_id: int) -> None:
        """清理训练任务相关文件"""
        from app.core.config import settings
        
        # 清理上传文件
        upload_patterns = [
            f"*job_{job_id}*",
            f"*{job_id}_*"
        ]
        
        for pattern in upload_patterns:
            import glob
            files = glob.glob(os.path.join(settings.UPLOAD_DIR, pattern))
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"删除文件 {file_path} 失败: {e}")
        
        # 清理模型文件
        model_patterns = [
            f"job_{job_id}",
            f"model_{job_id}"
        ]
        
        for pattern in model_patterns:
            model_path = os.path.join(settings.MODEL_DIR, pattern)
            if os.path.exists(model_path):
                try:
                    if os.path.isfile(model_path):
                        os.remove(model_path)
                    elif os.path.isdir(model_path):
                        shutil.rmtree(model_path)
                except Exception as e:
                    print(f"删除模型 {model_path} 失败: {e}")
    
    def estimate_training_time(self, 
                             model_name: str, 
                             dataset_size: int, 
                             epochs: int, 
                             batch_size: int) -> Dict[str, Any]:
        """估算训练时间"""
        # 基于模型大小和数据集大小的粗略估算
        model_factors = {
            "meta-llama/Llama-2-7b-chat-hf": 1.0,
            "bigcode/starcoderbase-7b": 0.8,
            "microsoft/DialoGPT-medium": 0.3
        }
        
        base_time_per_sample = 0.1  # 每个样本基础训练时间（秒）
        model_factor = model_factors.get(model_name, 1.0)
        
        # 计算每个 epoch 的时间
        steps_per_epoch = max(1, dataset_size // batch_size)
        time_per_epoch = steps_per_epoch * base_time_per_sample * model_factor
        
        # 总训练时间
        total_time = time_per_epoch * epochs
        
        return {
            "estimated_total_seconds": total_time,
            "estimated_total_minutes": total_time / 60,
            "estimated_total_hours": total_time / 3600,
            "time_per_epoch_seconds": time_per_epoch,
            "steps_per_epoch": steps_per_epoch,
            "model_factor": model_factor
        }
    
    def validate_training_environment(self) -> Dict[str, Any]:
        """验证训练环境"""
        checks = {}
        overall_status = "ready"
        
        # 检查 GPU
        gpu_info = self.get_gpu_usage()
        if gpu_info["available"] and gpu_info["device_count"] > 0:
            checks["gpu"] = {
                "status": "ok",
                "message": f"发现 {gpu_info['device_count']} 个 GPU 设备"
            }
        else:
            checks["gpu"] = {
                "status": "warning",
                "message": "未发现 GPU 设备，将使用 CPU 训练（速度较慢）"
            }
            overall_status = "warning"
        
        # 检查磁盘空间
        disk_usage = self.get_disk_usage()
        free_gb = disk_usage["free"] / (1024**3)
        
        if free_gb < 1:
            checks["disk"] = {
                "status": "error",
                "message": f"磁盘空间不足：仅剩 {free_gb:.1f} GB"
            }
            overall_status = "error"
        elif free_gb < 5:
            checks["disk"] = {
                "status": "warning", 
                "message": f"磁盘空间较少：剩余 {free_gb:.1f} GB"
            }
            if overall_status == "ready":
                overall_status = "warning"
        else:
            checks["disk"] = {
                "status": "ok",
                "message": f"磁盘空间充足：剩余 {free_gb:.1f} GB"
            }
        
        # 检查内存
        memory_usage = self.get_memory_usage()
        free_gb = memory_usage["available"] / (1024**3)
        
        if free_gb < 2:
            checks["memory"] = {
                "status": "error",
                "message": f"内存不足：可用 {free_gb:.1f} GB"
            }
            overall_status = "error"
        elif free_gb < 4:
            checks["memory"] = {
                "status": "warning",
                "message": f"内存较少：可用 {free_gb:.1f} GB"
            }
            if overall_status == "ready":
                overall_status = "warning"
        else:
            checks["memory"] = {
                "status": "ok",
                "message": f"内存充足：可用 {free_gb:.1f} GB"
            }
        
        # 检查 Python 包
        required_packages = [
            "torch", "transformers", "peft", "accelerate", 
            "datasets", "tokenizers"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            checks["packages"] = {
                "status": "error",
                "message": f"缺少必要包: {', '.join(missing_packages)}"
            }
            overall_status = "error"
        else:
            checks["packages"] = {
                "status": "ok",
                "message": "所有必要包已安装"
            }
        
        return {
            "overall_status": overall_status,
            "checks": checks,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_training_recommendations(self, dataset_size: int, model_name: str) -> Dict[str, Any]:
        """获取训练建议"""
        recommendations = {}
        
        # 批次大小建议
        if dataset_size < 100:
            recommendations["batch_size"] = {
                "suggested": 2,
                "reason": "小数据集，使用较小批次"
            }
        elif dataset_size < 1000:
            recommendations["batch_size"] = {
                "suggested": 4,
                "reason": "中等数据集，平衡训练效率"
            }
        else:
            recommendations["batch_size"] = {
                "suggested": 8,
                "reason": "大数据集，可使用较大批次"
            }
        
        # 学习率建议
        if "llama" in model_name.lower():
            recommendations["learning_rate"] = {
                "suggested": 2e-4,
                "reason": "LLaMA 模型推荐学习率"
            }
        elif "starcoder" in model_name.lower():
            recommendations["learning_rate"] = {
                "suggested": 5e-5,
                "reason": "代码模型使用较低学习率"
            }
        else:
            recommendations["learning_rate"] = {
                "suggested": 1e-4,
                "reason": "通用模型默认学习率"
            }
        
        # Epochs 建议
        if dataset_size < 100:
            recommendations["epochs"] = {
                "suggested": 5,
                "reason": "小数据集需要更多轮次"
            }
        elif dataset_size < 1000:
            recommendations["epochs"] = {
                "suggested": 3,
                "reason": "中等数据集标准轮次"
            }
        else:
            recommendations["epochs"] = {
                "suggested": 2,
                "reason": "大数据集避免过拟合"
            }
        
        # LoRA 参数建议
        recommendations["lora_config"] = {
            "r": {
                "suggested": 16,
                "reason": "平衡参数效率和性能"
            },
            "alpha": {
                "suggested": 32,
                "reason": "标准 alpha 值"
            },
            "dropout": {
                "suggested": 0.1,
                "reason": "防止过拟合"
            }
        }
        
        return recommendations
