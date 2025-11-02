"""
模型管理相关 API
"""
import os
import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import models
from app.schemas.schemas import (
    ModelInfoResponse, PredictionRequest, PredictionResponse
)
from app.services.model_service import ModelService
from app.core.config import settings

router = APIRouter()


@router.get("/", response_model=List[ModelInfoResponse])
async def get_models(
    skip: int = 0,
    limit: int = 100,
    is_deployed: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """
    获取模型列表
    """
    query = db.query(models.ModelInfo)
    
    if is_deployed is not None:
        query = query.filter(models.ModelInfo.is_deployed == is_deployed)
    
    models_list = query.offset(skip).limit(limit).all()
    return models_list


@router.get("/{model_id}", response_model=ModelInfoResponse)
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """
    获取特定模型信息
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.get("/{model_id}/download")
async def download_model(model_id: int, db: Session = Depends(get_db)):
    """
    下载模型文件
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    if not os.path.exists(model.model_path):
        raise HTTPException(status_code=404, detail="模型文件不存在")
    
    # 创建 ZIP 文件包含整个模型目录
    model_service = ModelService()
    zip_path = model_service.create_model_package(model.model_path)
    
    return FileResponse(
        zip_path,
        media_type='application/zip',
        filename=f"model_{model_id}_{model.model_name.replace('/', '_')}.zip"
    )


@router.post("/{model_id}/deploy")
async def deploy_model(model_id: int, db: Session = Depends(get_db)):
    """
    部署模型为 API 服务
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    if model.is_deployed:
        raise HTTPException(status_code=400, detail="模型已经部署")
    
    if not os.path.exists(model.model_path):
        raise HTTPException(status_code=404, detail="模型文件不存在")
    
    try:
        model_service = ModelService()
        endpoint_url = await model_service.deploy_model(model_id, model.model_path)
        
        # 更新部署状态
        model.is_deployed = True
        model.api_endpoint = endpoint_url
        db.commit()
        
        return {
            "message": "模型部署成功",
            "endpoint": endpoint_url,
            "model_id": model_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型部署失败: {str(e)}")


@router.delete("/{model_id}/deploy")
async def undeploy_model(model_id: int, db: Session = Depends(get_db)):
    """
    取消部署模型
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    if not model.is_deployed:
        raise HTTPException(status_code=400, detail="模型未部署")
    
    try:
        model_service = ModelService()
        await model_service.undeploy_model(model_id)
        
        # 更新部署状态
        model.is_deployed = False
        model.api_endpoint = None
        db.commit()
        
        return {"message": "模型取消部署成功"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消部署失败: {str(e)}")


@router.post("/{model_id}/predict", response_model=PredictionResponse)
async def predict_with_model(
    model_id: int,
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """
    使用模型进行预测
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    if not model.is_deployed:
        raise HTTPException(status_code=400, detail="模型未部署，请先部署模型")
    
    try:
        model_service = ModelService()
        result = await model_service.predict(
            model_id=model_id,
            input_text=request.input_text,
            max_length=request.max_length,
            temperature=request.temperature,
            top_p=request.top_p
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.delete("/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    """
    删除模型
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        # 如果模型已部署，先取消部署
        if model.is_deployed:
            model_service = ModelService()
            await model_service.undeploy_model(model_id)
        
        # 删除模型文件
        if os.path.exists(model.model_path):
            import shutil
            if os.path.isdir(model.model_path):
                shutil.rmtree(model.model_path)
            else:
                os.remove(model.model_path)
        
        # 删除数据库记录
        db.delete(model)
        db.commit()
        
        return {"message": "模型删除成功"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除模型失败: {str(e)}")


@router.get("/{model_id}/config")
async def get_model_config(model_id: int, db: Session = Depends(get_db)):
    """
    获取模型配置信息
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    # 读取模型配置文件
    config_path = os.path.join(model.model_path, "config.json")
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    else:
        config = model.config
    
    return {
        "model_id": model_id,
        "model_name": model.model_name,
        "model_path": model.model_path,
        "config": config,
        "is_deployed": model.is_deployed,
        "api_endpoint": model.api_endpoint
    }


@router.post("/{model_id}/validate")
async def validate_model(model_id: int, db: Session = Depends(get_db)):
    """
    验证模型完整性
    """
    model = db.query(models.ModelInfo).filter(models.ModelInfo.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    
    try:
        model_service = ModelService()
        validation_result = await model_service.validate_model(model.model_path)
        
        return {
            "model_id": model_id,
            "is_valid": validation_result["is_valid"],
            "validation_details": validation_result["details"],
            "file_size": validation_result.get("file_size"),
            "required_files": validation_result.get("required_files"),
            "missing_files": validation_result.get("missing_files", [])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"模型验证失败: {str(e)}")


@router.get("/supported/base-models")
async def get_supported_models():
    """
    获取支持的基础模型列表
    """
    return {
        "supported_models": settings.SUPPORTED_MODELS,
        "model_info": {
            "meta-llama/Llama-2-7b-chat-hf": {
                "description": "Meta LLaMA 2 7B Chat 模型",
                "size": "7B parameters",
                "type": "chat",
                "requires_auth": True
            },
            "bigcode/starcoderbase-7b": {
                "description": "StarCoder 7B 代码生成模型",
                "size": "7B parameters", 
                "type": "code",
                "requires_auth": False
            },
            "microsoft/DialoGPT-medium": {
                "description": "DialoGPT 对话生成模型",
                "size": "345M parameters",
                "type": "chat",
                "requires_auth": False
            }
        }
    }
