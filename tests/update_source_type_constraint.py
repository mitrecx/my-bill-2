#!/usr/bin/env python3
"""
更新数据库约束以支持微信账单
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine, text
from config.settings import settings

def update_source_type_constraint():
    """更新source_type约束以包含wechat"""
    try:
        # 连接数据库
        database_url = settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # 开始事务
            trans = conn.begin()
            
            try:
                # 删除旧的约束
                print("删除旧的source_type约束...")
                conn.execute(text("ALTER TABLE bills DROP CONSTRAINT IF EXISTS check_source_type;"))
                
                # 创建新的约束，包含wechat
                print("创建新的source_type约束，包含wechat...")
                conn.execute(text("""
                    ALTER TABLE bills 
                    ADD CONSTRAINT check_source_type 
                    CHECK (source_type IN ('alipay', 'jd', 'cmb', 'wechat'));
                """))
                
                # 提交事务
                trans.commit()
                print("✓ 约束更新成功！现在支持微信账单了。")
                
                # 验证新约束
                result = conn.execute(text("""
                    SELECT pg_get_constraintdef(oid) as constraint_definition
                    FROM pg_constraint 
                    WHERE conname = 'check_source_type'
                    AND conrelid = (SELECT oid FROM pg_class WHERE relname = 'bills');
                """))
                
                row = result.fetchone()
                if row:
                    print(f"新约束定义: {row[0]}")
                
            except Exception as e:
                trans.rollback()
                raise e
                
    except Exception as e:
        print(f"更新约束失败: {e}")

if __name__ == "__main__":
    update_source_type_constraint()