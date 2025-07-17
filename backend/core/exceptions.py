from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import traceback
from typing import Union
from config.logging import get_logger
from schemas.common import ApiResponse

logger = get_logger(__name__)


class AppException(Exception):
    """应用自定义异常基类"""
    
    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict = None
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationException(AppException):
    """数据验证异常"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details
        )


class AuthenticationException(AppException):
    """认证异常"""
    
    def __init__(self, message: str = "认证失败"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="AUTHENTICATION_ERROR"
        )


class AuthorizationException(AppException):
    """授权异常"""
    
    def __init__(self, message: str = "权限不足"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="AUTHORIZATION_ERROR"
        )


class ResourceNotFoundException(AppException):
    """资源未找到异常"""
    
    def __init__(self, message: str = "资源未找到"):
        super().__init__(
            message=message,
            status_code=404,
            error_code="RESOURCE_NOT_FOUND"
        )


class BusinessException(AppException):
    """业务逻辑异常"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(
            message=message,
            status_code=400,
            error_code="BUSINESS_ERROR",
            details=details
        )


class DatabaseConnectionException(AppException):
    """数据库连接异常"""
    
    def __init__(self, message: str = "数据库连接失败，请稍后重试"):
        super().__init__(
            message=message,
            status_code=503,
            error_code="DATABASE_CONNECTION_ERROR"
        )


def setup_exception_handlers(app: FastAPI):
    """设置全局异常处理器"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """处理应用自定义异常"""
        logger.error(
            "应用异常",
            error_code=exc.error_code,
            message=exc.message,
            status_code=exc.status_code,
            details=exc.details,
            path=request.url.path,
            method=request.method
        )
        
        response_data = ApiResponse(
            success=False,
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data.model_dump(mode='json')
        )
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """处理HTTP异常"""
        logger.warning(
            "HTTP异常",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method
        )
        
        response_data = ApiResponse(
            success=False,
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data.model_dump(mode='json')
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """处理请求验证异常"""
        errors = []
        for error in exc.errors():
            errors.append({
                "field": " -> ".join(str(x) for x in error["loc"]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        logger.warning(
            "请求验证失败",
            errors=errors,
            path=request.url.path,
            method=request.method
        )
        
        response_data = ApiResponse(
            success=False,
            message="请求数据验证失败",
            error_code="VALIDATION_ERROR",
            details={"errors": errors}
        )
        
        return JSONResponse(
            status_code=422,
            content=response_data.model_dump(mode='json')
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def starlette_exception_handler(request: Request, exc: StarletteHTTPException):
        """处理Starlette HTTP异常"""
        logger.warning(
            "Starlette HTTP异常",
            status_code=exc.status_code,
            detail=exc.detail,
            path=request.url.path,
            method=request.method
        )
        
        response_data = ApiResponse(
            success=False,
            message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data.model_dump(mode='json')
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """处理未捕获的异常"""
        error_id = id(exc)  # 生成错误ID用于追踪
        
        # 检查是否为数据库连接错误
        exc_str = str(exc).lower()
        if any(keyword in exc_str for keyword in [
            'connection refused', 
            'connection to server', 
            'could not connect to server',
            'database connection',
            'psycopg2.operationalerror',
            'connection timeout'
        ]):
            logger.error(
                "数据库连接异常",
                error_id=error_id,
                exception_type=type(exc).__name__,
                exception_message=str(exc),
                path=request.url.path,
                method=request.method
            )
            
            response_data = ApiResponse(
                success=False,
                message="数据库服务暂时不可用，请稍后重试",
                error_code="DATABASE_CONNECTION_ERROR",
                details={
                    "error_id": error_id,
                    "suggestion": "请检查数据库服务是否正常运行"
                }
            )
            
            return JSONResponse(
                status_code=503,
                content=response_data.model_dump(mode='json')
            )
        
        logger.error(
            "未处理异常",
            error_id=error_id,
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            traceback=traceback.format_exc(),
            path=request.url.path,
            method=request.method
        )
        
        response_data = ApiResponse(
            success=False,
            message="服务器内部错误",
            error_code="INTERNAL_SERVER_ERROR",
            details={"error_id": error_id}
        )
        
        return JSONResponse(
            status_code=500,
            content=response_data.model_dump(mode='json')
        )