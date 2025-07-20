#!/usr/bin/env python3
"""
数据库迁移脚本：删除bills表中的family_id字段
由于用户与家庭现在是一对一关系，可以通过user_id来确定家庭
"""

import psycopg2
import logging
import os
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """获取PostgreSQL数据库连接"""
    # 从环境变量获取数据库连接信息
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/family_bills')
    return psycopg2.connect(database_url)

def migrate_bills_table():
    """删除bills表中的family_id字段"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查bills表是否存在family_id字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bills' AND column_name = 'family_id'
        """)
        family_id_exists = cursor.fetchone()
        
        if not family_id_exists:
            logger.info("bills表中没有family_id字段，无需迁移")
            return
        
        logger.info("开始迁移bills表...")
        
        # PostgreSQL中直接删除列
        cursor.execute("ALTER TABLE bills DROP COLUMN IF EXISTS family_id")
        
        conn.commit()
        logger.info("bills表迁移完成，已删除family_id字段")
        
        # 验证迁移结果
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bills' AND column_name = 'family_id'
        """)
        family_id_still_exists = cursor.fetchone()
        
        if not family_id_still_exists:
            logger.info("验证成功：family_id字段已从bills表中删除")
        else:
            logger.error("验证失败：family_id字段仍然存在")
        
        # 检查数据完整性
        cursor.execute("SELECT COUNT(*) FROM bills")
        bill_count = cursor.fetchone()[0]
        logger.info(f"bills表中共有 {bill_count} 条记录")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def migrate_bill_categories_table():
    """删除bill_categories表中的family_id字段"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查bill_categories表是否存在family_id字段
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bill_categories' AND column_name = 'family_id'
        """)
        family_id_exists = cursor.fetchone()
        
        if not family_id_exists:
            logger.info("bill_categories表中没有family_id字段，无需迁移")
            return
        
        logger.info("开始迁移bill_categories表...")
        
        # PostgreSQL中直接删除列
        cursor.execute("ALTER TABLE bill_categories DROP COLUMN IF EXISTS family_id")
        
        conn.commit()
        logger.info("bill_categories表迁移完成，已删除family_id字段")
        
        # 验证迁移结果
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bill_categories' AND column_name = 'family_id'
        """)
        family_id_still_exists = cursor.fetchone()
        
        if not family_id_still_exists:
            logger.info("验证成功：family_id字段已从bill_categories表中删除")
        else:
            logger.error("验证失败：family_id字段仍然存在")
        
        # 检查数据完整性
        cursor.execute("SELECT COUNT(*) FROM bill_categories")
        category_count = cursor.fetchone()[0]
        logger.info(f"bill_categories表中共有 {category_count} 条记录")
        
    except Exception as e:
        logger.error(f"迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("开始数据库迁移：删除family_id字段")
    
    # 迁移bills表
    migrate_bills_table()
    
    # 迁移bill_categories表
    migrate_bill_categories_table()
    
    logger.info("数据库迁移完成")