from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List, Union
from datetime import datetime


class ApiResponse(BaseModel):
    """统一API响应格式"""
    success: bool = Field(..., description="请求是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="响应数据")
    error_code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(BaseModel):
    """分页响应格式"""
    items: List[Any] = Field(..., description="数据列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_prev: bool = Field(..., description="是否有上一页")
    
    @classmethod
    def create(
        cls,
        items: List[Any],
        total: int,
        page: int,
        size: int
    ) -> "PaginatedResponse":
        """创建分页响应"""
        pages = (total + size - 1) // size if size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态")
    version: str = Field(..., description="版本号")
    environment: str = Field(..., description="运行环境")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    services: Dict[str, Dict[str, Union[str, bool, float]]] = Field(
        default_factory=dict, 
        description="依赖服务状态"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MetricsResponse(BaseModel):
    """监控指标响应"""
    uptime: float = Field(..., description="运行时间（秒）")
    memory_usage: Dict[str, float] = Field(..., description="内存使用情况")
    cpu_usage: float = Field(..., description="CPU使用率")
    request_count: int = Field(..., description="请求总数")
    error_count: int = Field(..., description="错误总数")
    active_connections: int = Field(..., description="活跃连接数")
    timestamp: datetime = Field(default_factory=datetime.now, description="采集时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }