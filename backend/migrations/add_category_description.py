#!/usr/bin/env python3
"""
为bill_categories表添加description字段的数据库迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.settings import settings

def add_category_description():
    """为bill_categories表添加description字段"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 开始事务
        trans = conn.begin()
        
        try:
            # 检查字段是否已存在
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'bill_categories' 
                AND column_name = 'description'
            """))
            
            if result.fetchone():
                print("description字段已存在，跳过添加")
                return
            
            # 添加description字段
            print("为bill_categories表添加description字段...")
            conn.execute(text("""
                ALTER TABLE bill_categories 
                ADD COLUMN description VARCHAR(500)
            """))
            
            # 提交事务
            trans.commit()
            print("description字段添加成功！")
            
        except Exception as e:
            # 回滚事务
            trans.rollback()
            print(f"添加字段失败: {e}")
            raise

if __name__ == "__main__":
    print("开始添加description字段...")
    add_category_description()
    print("添加完成！") 