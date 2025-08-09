"""
数据库迁移脚本：删除 bills 表中的 counter_party 字段
注意：raw_data 中的 counter_party 字段保留不变
"""

import psycopg2
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def get_db_connection():
    """获取数据库连接"""
    # 从 DATABASE_URL 解析连接信息
    database_url = os.getenv("DATABASE_URL", "postgresql://josie:bills_password_2024@localhost:5432/bills_db")
    
    # 解析 DATABASE_URL
    import re
    match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
    if match:
        user, password, host, port, database = match.groups()
        return psycopg2.connect(
            host=host,
            port=int(port),
            database=database,
            user=user,
            password=password
        )
    else:
        # 回退到环境变量
        return psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "bills_db"),
            user=os.getenv("DB_USER", "josie"),
            password=os.getenv("DB_PASSWORD", "bills_password_2024")
        )

def remove_counter_party_field():
    """删除 bills 表中的 counter_party 字段"""
    conn = None
    cursor = None
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查字段是否存在
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'bills' AND column_name = 'counter_party'
        """)
        
        if cursor.fetchone():
            print("正在删除 bills 表中的 counter_party 字段...")
            
            # 删除 counter_party 字段
            cursor.execute("ALTER TABLE bills DROP COLUMN IF EXISTS counter_party")
            
            conn.commit()
            print("✅ 成功删除 counter_party 字段")
        else:
            print("ℹ️  counter_party 字段不存在，无需删除")
            
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ 删除字段时出错: {e}")
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    print("开始执行数据库迁移：删除 bills 表中的 counter_party 字段")
    remove_counter_party_field()
    print("迁移完成")