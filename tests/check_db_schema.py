#!/usr/bin/env python3
"""
检查数据库表结构
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from config.settings import settings

def check_bills_table_schema():
    """检查bills表的结构"""
    try:
        # 连接数据库
        database_url = settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 查询bills表的列信息
            result = conn.execute(text("""
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'bills' 
                ORDER BY ordinal_position;
            """))
            
            print("Bills表结构:")
            print("-" * 80)
            print(f"{'列名':<20} {'数据类型':<20} {'最大长度':<10} {'可空':<10}")
            print("-" * 80)
            
            for row in result:
                column_name = row[0]
                data_type = row[1]
                max_length = row[2] if row[2] else "无限制"
                is_nullable = row[3]
                print(f"{column_name:<20} {data_type:<20} {max_length:<10} {is_nullable:<10}")
                
    except Exception as e:
        print(f"检查表结构失败: {e}")

if __name__ == "__main__":
    check_bills_table_schema()