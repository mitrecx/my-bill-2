#!/usr/bin/env python3
"""
数据库迁移脚本：添加is_admin字段
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from config.database import engine
from config.settings import settings

def run_migration():
    """执行数据库迁移"""
    print("开始执行数据库迁移：添加is_admin字段...")
    
    try:
        with engine.connect() as connection:
            # 开始事务
            trans = connection.begin()
            
            try:
                # 检查is_admin字段是否已存在
                result = connection.execute(text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='is_admin'
                """))
                
                if result.fetchone():
                    print("is_admin字段已存在，跳过迁移")
                    trans.rollback()
                    return
                
                # 添加is_admin字段
                print("添加is_admin字段...")
                connection.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"))
                
                # 将test用户设置为管理员
                print("设置test用户为管理员...")
                result = connection.execute(text("UPDATE users SET is_admin = TRUE WHERE username = 'test'"))
                print(f"更新了 {result.rowcount} 个用户")
                
                # 提交事务
                trans.commit()
                print("数据库迁移完成！")
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"迁移失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_migration()