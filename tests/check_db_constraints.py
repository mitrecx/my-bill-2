#!/usr/bin/env python3
"""
检查数据库约束
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from config.settings import settings

def check_constraints():
    """检查数据库约束"""
    try:
        # 连接数据库
        database_url = settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 查询bills表的约束
            result = conn.execute(text("""
                SELECT 
                    conname as constraint_name,
                    contype as constraint_type,
                    pg_get_constraintdef(oid) as constraint_definition
                FROM pg_constraint 
                WHERE conrelid = (
                    SELECT oid FROM pg_class WHERE relname = 'bills'
                )
                ORDER BY conname;
            """))
            
            print("Bills表的约束:")
            print("-" * 100)
            
            for row in result:
                constraint_name = row[0]
                constraint_type = row[1]
                constraint_def = row[2]
                
                type_map = {
                    'c': 'CHECK',
                    'f': 'FOREIGN KEY',
                    'p': 'PRIMARY KEY',
                    'u': 'UNIQUE'
                }
                
                print(f"约束名: {constraint_name}")
                print(f"类型: {type_map.get(constraint_type, constraint_type)}")
                print(f"定义: {constraint_def}")
                print("-" * 100)
                
    except Exception as e:
        print(f"检查约束失败: {e}")

if __name__ == "__main__":
    check_constraints()