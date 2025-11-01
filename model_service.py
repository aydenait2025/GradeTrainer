"""
模型服务
"""
import os
import json
import shutil
import zipfile
import time
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import subprocess
import signal

from app.schemas.schemas import PredictionResponse
from app.core.config import settings


class ModelService:
    """模型服务"""
    
    def __init__(self):
        self.deployed_models = {}  # 存储已部署模型的进程信息
        self.base_port = 8100  # API 服务的起始端口
    
    def create_model_package(self, model_path: str) -> str:
        """创建模型下载包"""
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
        
        # 创建临时目录
        temp_dir = os.path.join(settings.MODEL_DIR, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # ZIP 文件路径
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"model_package_{timestamp}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)
        
        # 创建 ZIP 文件
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if os.path.isdir(model_path):
                # 打包整个目录
                for root, dirs, files in os.walk(model_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, model_path)
                        zipf.write(file_path, arcname)
            else:
                # 单个文件
                zipf.write(model_path, os.path.basename(model_path))
        
        return zip_path
    
    async def deploy_model(self, model_id: int, model_path: str) -> str:
        """部署模型为 API 服务"""
        if model_id in self.deployed_models:
            raise ValueError(f"模型 {model_id} 已经部署")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"模型路径不存在: {model_path}")
        
        # 分配端口
        port = self.base_port + model_id
        
        # 创建部署脚本
        deployment_script = self._create_deployment_script(model_path, port)
        
        # 启动模型服务
        try:
            process = await self._start_model_server(deployment_script, port)
            
            # 等待服务启动
            await self._wait_for_service(port, timeout=60)
            
            # 记录部署信息
            endpoint_url = f"http://localhost:{port}"
            self.deployed_models[model_id] = {
                "process": process,
                "port": port,
                "endpoint": endpoint_url,
                "model_path": model_path,
                "deployed_at": datetime.now()
            }
            
            return endpoint_url
            
        except Exception as e:
            # 清理失败的部署
            if model_id in self.deployed_models:
                await self.undeploy_model(model_id)
            raise e
    
    async def undeploy_model(self, model_id: int) -> None:
        """取消模型部署"""
        if model_id not in self.deployed_models:
            raise ValueError(f"模型 {model_id} 未部署")
        
        deployment_info = self.deployed_models[model_id]
        process = deployment_info["process"]
        
        try:
            # 优雅关闭
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=10.0)
            except asyncio.TimeoutError:
                # 强制杀死
                process.kill()
                await process.wait()
        except Exception as e:
            print(f"关闭模型服务时出错: {e}")
        
        # 从记录中移除
        del self.deployed_models[model_id]
    
    async def predict(self, 
                     model_id: int,
                     input_text: str,
                     max_length: int = 512,
                     temperature: float = 0.7,
                     top_p: float = 0.9) -> PredictionResponse:
        """使用部署的模型进行预测"""
        if model_id not in self.deployed_models:
            raise ValueError(f"模型 {model_id} 未部署")
        
        deployment_info = self.deployed_models[model_id]
        endpoint = deployment_info["endpoint"]
        
        # 发送预测请求
        import httpx
        
        start_time = time.time()
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{endpoint}/predict",
                    json={
                        "input_text": input_text,
                        "max_length": max_length,
                        "temperature": temperature,
                        "top_p": top_p
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                
                processing_time = time.time() - start_time
                
                return PredictionResponse(
                    input_text=input_text,
                    generated_text=result["generated_text"],
                    confidence=result.get("confidence"),
                    processing_time=processing_time
                )
                
            except httpx.RequestError as e:
                raise RuntimeError(f"模型预测请求失败: {e}")
            except httpx.HTTPStatusError as e:
                raise RuntimeError(f"模型预测 HTTP 错误: {e.status_code}")
    
    async def validate_model(self, model_path: str) -> Dict[str, Any]:
        """验证模型完整性"""
        if not os.path.exists(model_path):
            return {
                "is_valid": False,
                "details": "模型路径不存在"
            }
        
        validation_result = {
            "is_valid": True,
            "details": [],
            "required_files": [],
            "missing_files": [],
            "file_size": 0
        }
        
        # 检查必要文件
        if os.path.isdir(model_path):
            required_files = [
                "config.json",
                "pytorch_model.bin",  # 或 model.safetensors
                "tokenizer.json",     # 或 tokenizer_config.json
            ]
            
            validation_result["required_files"] = required_files
            
            existing_files = os.listdir(model_path)
            missing_files = []
            
            for req_file in required_files:
                if req_file not in existing_files:
                    # 检查替代文件
                    if req_file == "pytorch_model.bin" and "model.safetensors" in existing_files:
                        continue
                    elif req_file == "tokenizer.json" and "tokenizer_config.json" in existing_files:
                        continue
                    else:
                        missing_files.append(req_file)
            
            validation_result["missing_files"] = missing_files
            
            if missing_files:
                validation_result["is_valid"] = False
                validation_result["details"].append(f"缺少文件: {', '.join(missing_files)}")
            
            # 计算总大小
            total_size = 0
            for root, dirs, files in os.walk(model_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(file_path)
                    except OSError:
                        pass
            
            validation_result["file_size"] = total_size
            
            # 验证配置文件
            config_path = os.path.join(model_path, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r') as f:
                        config = json.load(f)
                    validation_result["details"].append("配置文件格式正确")
                except json.JSONDecodeError:
                    validation_result["is_valid"] = False
                    validation_result["details"].append("配置文件格式错误")
        else:
            # 单个文件
            validation_result["file_size"] = os.path.getsize(model_path)
            validation_result["details"].append("单个模型文件")
        
        return validation_result
    
    def _create_deployment_script(self, model_path: str, port: int) -> str:
        """创建模型部署脚本"""
        script_content = f'''
import os
import sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# 模型配置
MODEL_PATH = "{model_path}"
PORT = {port}

# 请求模型
class PredictRequest(BaseModel):
    input_text: str
    max_length: int = 512
    temperature: float = 0.7
    top_p: float = 0.9

# 创建 FastAPI 应用
app = FastAPI(title="Model API", version="1.0.0")

# 全局变量存储模型和分词器
tokenizer = None
model = None

@app.on_event("startup")
async def load_model():
    global tokenizer, model
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None
        )
        print(f"模型加载成功: {{MODEL_PATH}}")
    except Exception as e:
        print(f"模型加载失败: {{e}}")
        sys.exit(1)

@app.post("/predict")
async def predict(request: PredictRequest):
    try:
        inputs = tokenizer.encode(request.input_text, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=request.max_length,
                temperature=request.temperature,
                top_p=request.top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        return {{
            "generated_text": generated_text,
            "input_length": len(request.input_text),
            "output_length": len(generated_text)
        }}
    except Exception as e:
        return {{"error": str(e)}}

@app.get("/health")
async def health():
    return {{"status": "healthy", "model_loaded": model is not None}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT)
'''
        
        # 保存脚本
        script_dir = os.path.join(settings.MODEL_DIR, "deployment_scripts")
        os.makedirs(script_dir, exist_ok=True)
        
        script_path = os.path.join(script_dir, f"deploy_model_{port}.py")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return script_path
    
    async def _start_model_server(self, script_path: str, port: int) -> asyncio.subprocess.Process:
        """启动模型服务器"""
        cmd = [
            "python", script_path
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        return process
    
    async def _wait_for_service(self, port: int, timeout: int = 60) -> None:
        """等待服务启动"""
        import httpx
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"http://localhost:{port}/health",
                        timeout=5.0
                    )
                    if response.status_code == 200:
                        return
            except (httpx.RequestError, httpx.HTTPStatusError):
                pass
            
            await asyncio.sleep(2)
        
        raise TimeoutError(f"服务启动超时: port {port}")
    
    def get_deployed_models_info(self) -> Dict[int, Dict[str, Any]]:
        """获取已部署模型信息"""
        info = {}
        for model_id, deployment in self.deployed_models.items():
            info[model_id] = {
                "endpoint": deployment["endpoint"],
                "port": deployment["port"],
                "model_path": deployment["model_path"],
                "deployed_at": deployment["deployed_at"].isoformat(),
                "is_running": deployment["process"].returncode is None
            }
        return info
    
    async def cleanup_all_deployments(self) -> None:
        """清理所有部署"""
        model_ids = list(self.deployed_models.keys())
        for model_id in model_ids:
            try:
                await self.undeploy_model(model_id)
            except Exception as e:
                print(f"清理模型 {model_id} 时出错: {e}")
