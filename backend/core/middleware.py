import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from config.logging import get_logger
from api.health import increment_request_count, increment_error_count

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """请求日志中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 增加请求计数
        increment_request_count()
        
        # 记录请求信息
        logger.info(
            "请求开始",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
        
        try:
            # 处理请求
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应信息
            logger.info(
                "请求完成",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time * 1000, 2),  # 毫秒
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            
            return response
            
        except Exception as e:
            # 增加错误计数
            increment_error_count()
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误信息
            logger.error(
                "请求处理异常",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=round(process_time * 1000, 2),
            )
            
            # 重新抛出异常，让异常处理器处理
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # 添加安全头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 在生产环境添加HSTS
        if hasattr(request.app.state, "settings") and request.app.state.settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """简单的速率限制中间件"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()
        
        # 清理过期记录
        self.clients = {
            ip: timestamps for ip, timestamps in self.clients.items()
            if any(t > current_time - self.period for t in timestamps)
        }
        
        # 检查当前客户端的请求频率
        if client_ip in self.clients:
            # 过滤最近时间段内的请求
            recent_requests = [
                t for t in self.clients[client_ip]
                if t > current_time - self.period
            ]
            
            if len(recent_requests) >= self.calls:
                logger.warning(
                    "速率限制触发",
                    client_ip=client_ip,
                    request_count=len(recent_requests),
                    limit=self.calls
                )
                
                from fastapi.responses import JSONResponse
                from schemas.common import ApiResponse
                
                return JSONResponse(
                    status_code=429,
                    content=ApiResponse(
                        success=False,
                        message="请求过于频繁，请稍后再试",
                        error_code="RATE_LIMIT_EXCEEDED"
                    ).dict()
                )
            
            self.clients[client_ip] = recent_requests + [current_time]
        else:
            self.clients[client_ip] = [current_time]
        
        return await call_next(request)