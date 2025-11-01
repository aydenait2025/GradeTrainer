"""
文件上传相关 API
"""
import os
import zipfile
import json
from typing import List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
import pandas as pd
import aiofiles

from app.db.database import get_db
from app.schemas.schemas import FileUploadResponse, ErrorResponse
from app.core.config import settings
from app.services.data_processor import DataProcessor

router = APIRouter()


@router.post("/file", response_model=FileUploadResponse)
async def upload_training_data(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    上传训练数据文件
    
    支持格式：
    - ZIP 文件（包含作业文件和评分 CSV）
    - 单个 CSV 文件
    """
    # 检查文件大小
    if file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"文件大小超过限制 ({settings.MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB)"
        )
    
    # 检查文件格式
    allowed_extensions = ['.zip', '.csv', '.xlsx']
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式。支持的格式: {', '.join(allowed_extensions)}"
        )
    
    # 创建上传目录
    upload_dir = os.path.join(settings.UPLOAD_DIR, datetime.now().strftime("%Y%m%d_%H%M%S"))
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存上传文件
    file_path = os.path.join(upload_dir, file.filename)
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    try:
        # 处理不同类型的文件
        data_preview = None
        processor = DataProcessor()
        
        if file_extension == '.zip':
            data_preview = await process_zip_file(file_path, upload_dir, processor)
        elif file_extension in ['.csv', '.xlsx']:
            data_preview = await process_spreadsheet_file(file_path, processor)
        
        return FileUploadResponse(
            filename=file.filename,
            file_path=file_path,
            file_size=file.size,
            upload_time=datetime.now(),
            data_preview=data_preview
        )
        
    except Exception as e:
        # 清理上传的文件
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"文件处理失败: {str(e)}")


async def process_zip_file(file_path: str, extract_dir: str, processor: DataProcessor) -> Dict[str, Any]:
    """处理 ZIP 文件"""
    extracted_dir = os.path.join(extract_dir, "extracted")
    
    # 解压文件
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extracted_dir)
    
    # 查找 CSV 文件和作业文件
    csv_files = []
    assignment_files = []
    
    for root, dirs, files in os.walk(extracted_dir):
        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.csv'):
                csv_files.append(file_path)
            elif file.endswith(('.txt', '.md', '.pdf', '.docx')):
                assignment_files.append(file_path)
    
    if not csv_files:
        raise ValueError("ZIP 文件中未找到 CSV 评分文件")
    
    # 处理第一个 CSV 文件
    df = pd.read_csv(csv_files[0])
    
    # 验证 CSV 格式
    required_columns = ['student_id', 'assignment', 'score']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"CSV 文件缺少必要列: {missing_columns}")
    
    # 生成数据预览
    preview = {
        "csv_files": len(csv_files),
        "assignment_files": len(assignment_files),
        "total_records": len(df),
        "students": df['student_id'].nunique(),
        "assignments": df['assignment'].nunique(),
        "score_range": {
            "min": float(df['score'].min()),
            "max": float(df['score'].max()),
            "mean": float(df['score'].mean())
        },
        "sample_data": df.head(5).to_dict('records'),
        "column_names": list(df.columns)
    }
    
    return preview


async def process_spreadsheet_file(file_path: str, processor: DataProcessor) -> Dict[str, Any]:
    """处理电子表格文件"""
    # 读取文件
    if file_path.endswith('.csv'):
        df = pd.read_csv(file_path)
    else:  # .xlsx
        df = pd.read_excel(file_path)
    
    # 基本验证
    if len(df) == 0:
        raise ValueError("文件为空")
    
    # 生成数据预览
    preview = {
        "total_records": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "sample_data": df.head(5).to_dict('records'),
        "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict()
    }
    
    return preview


@router.get("/supported-formats")
async def get_supported_formats():
    """获取支持的文件格式信息"""
    return {
        "formats": [
            {
                "extension": ".zip",
                "description": "包含作业文件和评分 CSV 的压缩包",
                "requirements": [
                    "必须包含至少一个 CSV 文件",
                    "CSV 文件需要包含: student_id, assignment, score 列",
                    "可包含作业文件 (.txt, .md, .pdf, .docx)"
                ]
            },
            {
                "extension": ".csv",
                "description": "逗号分隔值文件",
                "requirements": [
                    "建议包含: student_id, assignment, score 列",
                    "使用 UTF-8 编码"
                ]
            },
            {
                "extension": ".xlsx",
                "description": "Excel 电子表格",
                "requirements": [
                    "建议包含: student_id, assignment, score 列",
                    "使用第一个工作表"
                ]
            }
        ],
        "max_size": f"{settings.MAX_UPLOAD_SIZE / 1024 / 1024:.1f}MB"
    }


@router.delete("/file/{file_path}")
async def delete_uploaded_file(file_path: str):
    """删除上传的文件"""
    full_path = os.path.join(settings.UPLOAD_DIR, file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="文件不存在")
    
    try:
        if os.path.isfile(full_path):
            os.remove(full_path)
        else:
            # 删除目录
            import shutil
            shutil.rmtree(full_path)
        
        return {"message": "文件删除成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")
