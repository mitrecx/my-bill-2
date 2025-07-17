from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager

# 导入配置和日志
from config.settings import settings
from config.logging import init_logging, get_logger

# 导入路由
from api import api_router

# 导入异常处理和中间件
from core.exceptions import setup_exception_handlers
from core.middleware import (
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    RateLimitMiddleware
)

# 导入响应模型
from schemas.common import ApiResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    init_logging()
    logger = get_logger(__name__)
    
    logger.info(
        "应用启动",
        environment=settings.ENVIRONMENT,
        debug=settings.DEBUG,
        version="1.0.0"
    )
    
    # 确保必要目录存在
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    yield
    
    # 关闭时清理
    logger.info("应用关闭")


# 创建FastAPI应用
app = FastAPI(
    title="Bills Management API",
    version="1.0.0",
    description="个人账单管理系统API",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None
)

# 存储设置到应用状态
app.state.settings = settings

# 设置异常处理器
setup_exception_handlers(app)

# CORS配置 - 必须在其他中间件之前
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加其他中间件（注意顺序）
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# 在生产环境启用速率限制
if settings.is_production:
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# 注册路由
app.include_router(api_router)


@app.get("/", response_model=ApiResponse)
async def root():
    """根路径"""
    return ApiResponse(
        success=True,
        message="Bills Management API",
        data={
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "docs_url": "/docs" if not settings.is_production else None
        }
    )


if __name__ == "__main__":
    # 使用settings配置启动服务器
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info",
        access_log=True
    )