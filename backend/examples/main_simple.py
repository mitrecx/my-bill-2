from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="家庭账单管理系统",
    description="多用户家庭账单管理系统API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS中间件 - 允许所有来源（用于测试）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 健康检查端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "账单管理系统运行正常",
        "version": "1.0.0",
        "cors": "enabled"
    }

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用多用户家庭账单管理系统",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# API v1 路由组
from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")

# 测试注册端点
@api_router.post("/auth/register")
async def register_test():
    """测试注册端点"""
    logger.info("收到注册请求")
    return {
        "success": True,
        "message": "CORS测试成功！注册功能暂时不可用，但连接正常",
        "data": {
            "user_id": 12345,
            "username": "test_user"
        }
    }

# 测试登录端点
@api_router.post("/auth/login")
async def login_test():
    """测试登录端点"""
    logger.info("收到登录请求")
    return {
        "success": True,
        "message": "CORS测试成功！登录功能暂时不可用，但连接正常",
        "data": {
            "access_token": "test_token_12345",
            "token_type": "bearer"
        }
    }

# 测试API端点
@api_router.get("/test")
async def test_api():
    """测试API连接"""
    return {
        "message": "API连接正常",
        "cors_enabled": True,
        "timestamp": "2024-01-01T00:00:00Z"
    }

# 注册API路由
app.include_router(api_router)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_simple:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )