from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class UploadResponse(BaseModel):
    """文件上传响应"""
    id: int
    filename: str
    file_size: int
    source_type: str
    upload_time: datetime
    success_count: int
    failed_count: int
    status: str
    message: str = None

class ParsePreviewResponse(BaseModel):
    """文件预览响应"""
    source_type: str
    total_records: int
    success_count: int
    failed_count: int
    preview_data: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    warnings: List[str]

class UploadHistoryResponse(BaseModel):
    """上传历史响应"""
    id: int
    filename: str
    file_size: int
    source_type: str
    upload_time: datetime
    success_count: int
    failed_count: int
    status: str
    message: str = None

class UploadStatsResponse(BaseModel):
    """上传统计响应"""
    total_uploads: int
    total_success: int
    total_failed: int
    total_processing: int
    by_source_type: Dict[str, int]
    recent_uploads: List[Dict[str, Any]]

class FileUploadResponse(BaseModel):
    """文件上传预览响应（匹配前端类型）"""
    filename: str
    preview: List[Dict[str, Any]]
    total_records: int
    upload_id: str

class FileUploadConfirm(BaseModel):
    """文件上传确认请求"""
    upload_id: str
    family_id: int