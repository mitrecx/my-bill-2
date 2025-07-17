"""
测试配置和共享fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# 导入应用和数据库相关模块
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from main import app
from config.database import get_db
from models.base import Base

# 测试数据库URL
TEST_DATABASE_URL = "postgresql+asyncpg://test_user:test_password@localhost:5432/test_bills_db"

# 创建测试数据库引擎
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """设置测试数据库"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def sample_bill_data():
    """示例账单数据"""
    return {
        "transaction_date": "2024-01-01",
        "amount": 100.50,
        "description": "测试账单",
        "category": "餐饮",
        "source_type": "manual"
    }