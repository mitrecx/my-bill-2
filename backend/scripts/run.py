#!/usr/bin/env python3
"""
账单管理系统后端启动脚本
"""

import os
import sys
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from config.settings import settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def check_environment():
    """检查运行环境"""
    logger.info("检查运行环境...")
    
    # 检查必要的环境变量
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"缺少必要的环境变量: {missing_vars}")
        logger.info("请设置以下环境变量:")
        logger.info("DATABASE_URL=postgresql://username:password@localhost:5432/bills_db")
        logger.info("SECRET_KEY=your-secret-key-here")
        return False
    
    # 创建日志目录
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # 创建上传目录
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(exist_ok=True)
    
    logger.info("环境检查完成")
    return True


def main():
    """主函数"""
    logger.info("启动账单管理系统后端服务...")
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 启动配置
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = settings.debug
    
    logger.info(f"服务配置:")
    logger.info(f"  - 主机: {host}")
    logger.info(f"  - 端口: {port}")
    logger.info(f"  - 调试模式: {reload}")
    logger.info(f"  - 数据库: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'PostgreSQL'}")
    
    # 启动服务器
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True,
            loop="asyncio"
        )
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )