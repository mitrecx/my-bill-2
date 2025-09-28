#!/usr/bin/env python3
"""
为 bill_categories 表添加 is_deleted 字段（BOOLEAN，默认 false）的数据库迁移脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.settings import settings


def add_is_deleted_column():
    """为 bill_categories 表添加 is_deleted 字段"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        trans = conn.begin()
        try:
            # 检查字段是否已存在
            result = conn.execute(text(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'bill_categories' 
                  AND column_name = 'is_deleted'
                """
            ))
            if result.fetchone():
                print("is_deleted 字段已存在，跳过添加")
                trans.commit()
                return

            print("为 bill_categories 表添加 is_deleted 字段...")
            conn.execute(text(
                """
                ALTER TABLE bill_categories 
                ADD COLUMN is_deleted BOOLEAN NOT NULL DEFAULT FALSE
                """
            ))

            # 为安全起见，确保现有数据全部为未删除状态
            conn.execute(text("UPDATE bill_categories SET is_deleted = FALSE WHERE is_deleted IS NULL"))

            trans.commit()
            print("is_deleted 字段添加成功！")
        except Exception as e:
            trans.rollback()
            print(f"添加 is_deleted 字段失败: {e}")
            raise


if __name__ == "__main__":
    print("开始添加 is_deleted 字段...")
    add_is_deleted_column()
    print("完成！")