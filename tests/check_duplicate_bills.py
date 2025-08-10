#!/usr/bin/env python3
"""
检查数据库中是否有重复的微信账单记录
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from config.settings import settings

def check_duplicate_bills():
    """检查重复的账单记录"""
    try:
        # 连接数据库
        database_url = settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 查询微信账单记录
            result = conn.execute(text("""
                SELECT user_id, transaction_time, amount, transaction_desc, source_type, COUNT(*) as count
                FROM bills 
                WHERE source_type = 'wechat'
                GROUP BY user_id, transaction_time, amount, transaction_desc, source_type
                HAVING COUNT(*) > 1
                ORDER BY count DESC;
            """))
            
            duplicates = result.fetchall()
            
            if duplicates:
                print("发现重复的微信账单记录:")
                print("-" * 100)
                for row in duplicates:
                    print(f"用户ID: {row[0]}, 时间: {row[1]}, 金额: {row[2]}, 描述: {row[3]}, 重复次数: {row[5]}")
            else:
                print("没有发现重复的微信账单记录")
            
            # 查询最近的微信账单记录
            print("\n最近的微信账单记录:")
            print("-" * 100)
            result = conn.execute(text("""
                SELECT id, user_id, transaction_time, amount, transaction_desc, created_at
                FROM bills 
                WHERE source_type = 'wechat'
                ORDER BY created_at DESC
                LIMIT 10;
            """))
            
            recent_bills = result.fetchall()
            for row in recent_bills:
                print(f"ID: {row[0]}, 用户ID: {row[1]}, 时间: {row[2]}, 金额: {row[3]}, 描述: {row[4]}, 创建时间: {row[5]}")
                
    except Exception as e:
        print(f"检查重复记录失败: {e}")

if __name__ == "__main__":
    check_duplicate_bills()