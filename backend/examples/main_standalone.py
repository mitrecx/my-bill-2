from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field, ValidationError
from passlib.context import CryptContext
import logging
import hashlib
import time
import json
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="家庭账单管理系统",
    description="多用户家庭账单管理系统API - 生产环境版本",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# 配置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# 自定义422错误处理器
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    errors = []
    for error in exc.errors():
        field = error.get('loc', ['unknown'])[-1]
        msg = error.get('msg', '验证失败')
        error_type = error.get('type', 'unknown')
        
        if error_type == 'missing':
            errors.append(f"缺少必需字段: {field}")
        elif error_type == 'value_error.any_str.min_length':
            errors.append(f"字段 {field} 不能为空")
        else:
            errors.append(f"字段 {field}: {msg}")
    
    return JSONResponse(
        status_code=422,
        content={
            "success": False,
            "message": "请求数据验证失败",
            "errors": errors,
            "detail": "请检查请求参数格式和必需字段"
        }
    )

# 数据库连接状态
DB_AVAILABLE = False
try:
    import psycopg2
    import sqlalchemy
    from sqlalchemy import create_engine, text
    
    # 测试数据库连接
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://josie:bills_password_2024@localhost:5432/bills_db")
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    DB_AVAILABLE = True
    logger.info("数据库连接成功")
except Exception as e:
    logger.warning(f"数据库连接失败，使用内存存储: {e}")

# 内存存储（用于测试和演示）
MEMORY_USERS = {}
MEMORY_SESSIONS = {}

# Pydantic模型
class UserRegister(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, description="用户名不能为空")
    password: str = Field(..., min_length=1, description="密码不能为空")

class User(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool = True

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 工具函数
def hash_password(password: str) -> str:
    """bcrypt密码哈希"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    # 兼容旧的SHA256格式
    if len(hashed_password) == 64 and not hashed_password.startswith('$'):
        # 这是SHA256格式，直接比较
        return hashed_password == hashlib.sha256(plain_password.encode()).hexdigest()
    # 使用bcrypt验证
    return pwd_context.verify(plain_password, hashed_password)

def verify_and_upgrade_password(plain_password: str, stored_hash: str, username: str) -> bool:
    """验证密码并自动升级格式"""
    # 验证密码
    if len(stored_hash) == 64 and not stored_hash.startswith('$'):
        # SHA256格式
        if stored_hash == hashlib.sha256(plain_password.encode()).hexdigest():
            # 密码正确，升级到bcrypt
            if DB_AVAILABLE:
                try:
                    new_hash = pwd_context.hash(plain_password)
                    with engine.connect() as conn:
                        conn.execute(
                            text("UPDATE users SET password_hash = :new_hash WHERE username = :username"),
                            {"new_hash": new_hash, "username": username}
                        )
                        conn.commit()
                    logger.info(f"用户 {username} 密码已自动升级到bcrypt")
                except Exception as e:
                    logger.error(f"升级用户 {username} 密码失败: {e}")
            return True
        return False
    else:
        # bcrypt格式
        return pwd_context.verify(plain_password, stored_hash)

def generate_token(user_id: int) -> str:
    """生成简单的token"""
    timestamp = str(int(time.time()))
    data = f"{user_id}:{timestamp}"
    return hashlib.md5(data.encode()).hexdigest()

def get_user_from_db(username: str):
    """从数据库获取用户"""
    if not DB_AVAILABLE:
        return MEMORY_USERS.get(username)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT id, username, email, full_name, is_active FROM users WHERE username = :username"),
                {"username": username}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1], 
                    "email": row[2],
                    "full_name": row[3],
                    "is_active": row[4]
                }
        return None
    except Exception as e:
        logger.error(f"查询用户失败: {e}")
        return None

def create_user_in_db(user_data: UserRegister):
    """创建用户"""
    if not DB_AVAILABLE:
        # 内存存储
        user_id = len(MEMORY_USERS) + 1
        user = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email, 
            "full_name": user_data.full_name,
            "password_hash": hash_password(user_data.password),
            "is_active": True
        }
        MEMORY_USERS[user_data.username] = user
        return user
    
    try:
        hashed_password = hash_password(user_data.password)
        with engine.connect() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO users (username, email, full_name, password_hash, is_active) 
                    VALUES (:username, :email, :full_name, :password_hash, :is_active)
                    RETURNING id, username, email, full_name, is_active
                """),
                {
                    "username": user_data.username,
                    "email": user_data.email,
                    "full_name": user_data.full_name,
                    "password_hash": hashed_password,
                    "is_active": True
                }
            )
            conn.commit()
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "email": row[2], 
                    "full_name": row[3],
                    "is_active": row[4]
                }
        return None
    except Exception as e:
        logger.error(f"创建用户失败: {e}")
        return None

# 安全相关
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户"""
    if not credentials:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    
    token = credentials.credentials
    user_info = MEMORY_SESSIONS.get(token)
    if not user_info:
        raise HTTPException(status_code=401, detail="无效的认证令牌")
    
    return user_info

# API端点
@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "message": "账单管理系统运行正常",
        "version": "1.0.0",
        "database": "connected" if DB_AVAILABLE else "memory_mode",
        "cors": "enabled"
    }

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用多用户家庭账单管理系统",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/api/v1/auth/register")
async def register(user_data: UserRegister):
    """用户注册"""
    logger.info(f"收到注册请求: {user_data.username}")
    
    # 检查用户是否已存在
    existing_user = get_user_from_db(user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    # 创建用户
    new_user = create_user_in_db(user_data)
    if not new_user:
        raise HTTPException(status_code=500, detail="创建用户失败")
    
    # 生成token
    token = generate_token(new_user["id"])
    MEMORY_SESSIONS[token] = new_user
    
    return {
        "success": True,
        "message": "注册成功",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": new_user["id"],
                "username": new_user["username"],
                "email": new_user["email"],
                "full_name": new_user["full_name"]
            }
        }
    }

@app.post("/api/v1/auth/login")
async def login(login_data: UserLogin):
    """用户登录"""
    logger.info(f"收到登录请求: {login_data.username}")
    
    # 验证用户
    user = get_user_from_db(login_data.username)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 验证密码
    if not DB_AVAILABLE:
        stored_hash = user.get("password_hash")
    else:
        try:
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT password_hash FROM users WHERE username = :username"),
                    {"username": login_data.username}
                )
                row = result.fetchone()
                stored_hash = row[0] if row else None
        except Exception as e:
            logger.error(f"查询密码失败: {e}")
            raise HTTPException(status_code=500, detail="登录失败")
    
    if not verify_and_upgrade_password(login_data.password, stored_hash, login_data.username):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    # 生成token
    token = generate_token(user["id"])
    MEMORY_SESSIONS[token] = user
    
    return {
        "success": True,
        "message": "登录成功",
        "data": {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"]
            }
        }
    }

@app.get("/api/v1/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """获取当前用户信息"""
    return {
        "success": True,
        "data": {
            "id": current_user["id"],
            "username": current_user["username"],
            "email": current_user["email"],
            "full_name": current_user["full_name"]
        }
    }

@app.get("/api/v1/test")
async def test_api():
    """测试API连接"""
    return {
        "message": "API连接正常",
        "cors_enabled": True,
        "database_status": "connected" if DB_AVAILABLE else "memory_mode",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# 简单的账单相关端点（演示用）
@app.get("/api/v1/bills/stats")
async def get_bills_stats(current_user: dict = Depends(get_current_user)):
    """获取账单统计"""
    return {
        "success": True,
        "data": {
            "total_income": 5000.00,
            "total_expense": 3500.00,
            "net_amount": 1500.00,
            "transaction_count": 25,
            "period": "本月"
        }
    }

@app.get("/api/v1/bills")
async def get_bills(page: int = 1, size: int = 10, current_user: dict = Depends(get_current_user)):
    """获取账单列表"""
    return {
        "success": True,
        "data": {
            "items": [
                {
                    "id": 1,
                    "amount": 88.50,
                    "transaction_type": "expense", 
                    "transaction_desc": "午餐支出",
                    "transaction_date": "2024-01-10",
                    "source_type": "alipay"
                }
            ],
            "total": 1,
            "page": page,
            "size": size,
            "pages": 1
        }
    }

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_production:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )