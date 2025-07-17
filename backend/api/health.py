import time
import psutil
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from config.settings import settings
from config.logging import get_logger
from schemas.common import HealthCheckResponse, MetricsResponse, ApiResponse
from config.database import get_db

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["健康检查"])

# 应用启动时间
app_start_time = time.time()

# 请求计数器
request_count = 0
error_count = 0


class HealthChecker:
    """健康检查器"""
    
    @staticmethod
    def check_database(db: Session) -> Dict[str, Any]:
        """检查数据库连接"""
        try:
            start_time = time.time()
            result = db.execute(text("SELECT 1"))
            response_time = time.time() - start_time
            
            return {
                "status": "healthy",
                "response_time": round(response_time * 1000, 2),  # 毫秒
                "message": "数据库连接正常"
            }
        except Exception as e:
            logger.error("数据库健康检查失败", error=str(e))
            return {
                "status": "unhealthy",
                "response_time": 0.0,  # 修复：使用0.0而不是None
                "message": f"数据库连接失败: {str(e)}"
            }
    
    @staticmethod
    def check_memory() -> Dict[str, Any]:
        """检查内存使用情况"""
        try:
            memory = psutil.virtual_memory()
            return {
                "status": "healthy" if memory.percent < 90 else "warning",
                "usage_percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2),
                "total_gb": round(memory.total / (1024**3), 2),
                "message": "内存使用正常" if memory.percent < 90 else "内存使用率较高"
            }
        except Exception as e:
            logger.error("内存检查失败", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"内存检查失败: {str(e)}"
            }
    
    @staticmethod
    def check_disk() -> Dict[str, Any]:
        """检查磁盘使用情况"""
        try:
            disk = psutil.disk_usage('/')
            usage_percent = (disk.used / disk.total) * 100
            
            return {
                "status": "healthy" if usage_percent < 85 else "warning",
                "usage_percent": round(usage_percent, 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "total_gb": round(disk.total / (1024**3), 2),
                "message": "磁盘空间充足" if usage_percent < 85 else "磁盘空间不足"
            }
        except Exception as e:
            logger.error("磁盘检查失败", error=str(e))
            return {
                "status": "unhealthy",
                "message": f"磁盘检查失败: {str(e)}"
            }


@router.get("/", response_model=ApiResponse)
async def health_check(db: Session = Depends(get_db)):
    """基础健康检查"""
    try:
        # 检查各个组件
        db_status = HealthChecker.check_database(db)
        memory_status = HealthChecker.check_memory()
        disk_status = HealthChecker.check_disk()
        
        # 判断整体状态
        all_healthy = all(
            status["status"] == "healthy" 
            for status in [db_status, memory_status, disk_status]
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        health_data = HealthCheckResponse(
            status=overall_status,
            version="1.0.0",
            environment=settings.ENVIRONMENT,
            services={
                "database": db_status,
                "memory": memory_status,
                "disk": disk_status
            }
        )
        
        logger.info("健康检查完成", status=overall_status)
        
        return ApiResponse(
            success=True,
            message="健康检查完成",
            data=health_data.dict()
        )
        
    except Exception as e:
        logger.error("健康检查失败", error=str(e))
        return ApiResponse(
            success=False,
            message="健康检查失败",
            error_code="HEALTH_CHECK_ERROR"
        )


@router.get("/live", response_model=ApiResponse)
async def liveness_check():
    """存活检查 - 用于K8s liveness probe"""
    return ApiResponse(
        success=True,
        message="服务正在运行",
        data={
            "status": "alive",
            "timestamp": datetime.now().isoformat()
        }
    )


@router.get("/ready", response_model=ApiResponse)
async def readiness_check(db: Session = Depends(get_db)):
    """就绪检查 - 用于K8s readiness probe"""
    try:
        # 检查数据库连接
        db_status = HealthChecker.check_database(db)
        
        if db_status["status"] == "healthy":
            return ApiResponse(
                success=True,
                message="服务已就绪",
                data={
                    "status": "ready",
                    "timestamp": datetime.now().isoformat()
                }
            )
        else:
            return ApiResponse(
                success=False,
                message="服务未就绪",
                data={
                    "status": "not_ready",
                    "reason": db_status["message"]
                }
            )
            
    except Exception as e:
        logger.error("就绪检查失败", error=str(e))
        return ApiResponse(
            success=False,
            message="就绪检查失败",
            error_code="READINESS_CHECK_ERROR"
        )


@router.get("/metrics", response_model=ApiResponse)
async def get_metrics():
    """获取监控指标"""
    try:
        # 计算运行时间
        uptime = time.time() - app_start_time
        
        # 获取内存信息
        memory = psutil.virtual_memory()
        memory_usage = {
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used
        }
        
        # 获取CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 获取网络连接数（近似活跃连接数）
        try:
            connections = len(psutil.net_connections())
        except:
            connections = 0
        
        metrics_data = MetricsResponse(
            uptime=uptime,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            request_count=request_count,
            error_count=error_count,
            active_connections=connections
        )
        
        return ApiResponse(
            success=True,
            message="监控指标获取成功",
            data=metrics_data.dict()
        )
        
    except Exception as e:
        logger.error("获取监控指标失败", error=str(e))
        return ApiResponse(
            success=False,
            message="获取监控指标失败",
            error_code="METRICS_ERROR"
        )


def increment_request_count():
    """增加请求计数"""
    global request_count
    request_count += 1


def increment_error_count():
    """增加错误计数"""
    global error_count
    error_count += 1