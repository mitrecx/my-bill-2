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
    
    # 检查settings是否正确加载
    try:
        # 尝试访问必要的配置
        database_url = settings.DATABASE_URL
        secret_key = settings.SECRET_KEY
        
        if not database_url or not secret_key:
            logger.error("配置文件中缺少必要的配置项")
            return False
            
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        logger.info("请检查配置文件或环境变量:")
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
    
    # 使用settings配置
    host = settings.HOST
    port = settings.PORT
    reload = settings.DEBUG
    
    logger.info(f"服务配置:")
    logger.info(f"  - 主机: {host}")
    logger.info(f"  - 端口: {port}")
    logger.info(f"  - 调试模式: {reload}")
    logger.info(f"  - 环境: {settings.ENVIRONMENT}")
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
    # 调用main函数以保持一致性
    main()