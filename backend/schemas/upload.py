from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class UploadResponse(BaseModel):
    """文件上传响应"""
    upload_id: int
    filename: str
    source_type: str
    total_records: int
    success_count: int  # 总成功数（新增+更新）
    created_count: int = 0  # 新增记录数
    updated_count: int = 0  # 更新记录数
    failed_count: int
    status: str
    created_bills: List[int] = []
    errors: List[str] = []
    warnings: List[str] = []

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

class UploadRecord(BaseModel):
    """上传记录响应（匹配前端UploadRecord类型）"""
    id: int
    family_id: int
    user_id: int
    filename: str
    file_size: int
    source_type: str
    records_count: int
    status: str
    error_message: Optional[str] = None
    uploaded_at: str
    processed_at: Optional[str] = None