#!/usr/bin/env python3
"""
PostgreSQL数据库设置脚本
用于初始化PostgreSQL数据库和表结构
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy import create_engine, text
from config.database import Base
from models.user import User
from models.family import Family, FamilyMember
from models.bill import Bill, BillCategory
from config.settings import settings

def create_database():
    """
    创建PostgreSQL数据库
    """
    # 从DATABASE_URL中提取连接信息
    db_url = settings.DATABASE_URL
    if not db_url.startswith('postgresql://'):
        print("错误：DATABASE_URL必须是PostgreSQL格式")
        return False
    
    # 解析数据库连接信息
    try:
        # postgresql://user:password@host:port/database
        url_parts = db_url.replace('postgresql://', '').split('/')
        db_name = url_parts[1] if len(url_parts) > 1 else 'bills_db'
        
        auth_host = url_parts[0]
        if '@' in auth_host:
            auth, host_port = auth_host.split('@')
            if ':' in auth:
                user, password = auth.split(':', 1)
            else:
                user, password = auth, ''
        else:
            user, password = 'postgres', ''
            host_port = auth_host
        
        if ':' in host_port:
            host, port = host_port.split(':')
        else:
            host, port = host_port, '5432'
        
        print(f"连接信息: 用户={user}, 主机={host}, 端口={port}, 数据库={db_name}")
        
        # 连接到PostgreSQL服务器（不指定数据库）
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database='postgres'  # 连接到默认数据库
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"创建数据库: {db_name}")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"数据库 {db_name} 创建成功！")
        else:
            print(f"数据库 {db_name} 已存在")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"创建数据库失败: {e}")
        return False

def create_tables():
    """
    创建数据库表
    """
    try:
        print("创建数据库表...")
        engine = create_engine(settings.DATABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("数据库表创建成功！")
        return True
    except Exception as e:
        print(f"创建表失败: {e}")
        return False

def run_init_sql():
    """
    运行初始化SQL脚本（插入默认分类等）
    """
    try:
        print("运行初始化SQL脚本...")
        engine = create_engine(settings.DATABASE_URL)
        
        # 读取初始化SQL文件
        init_sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'database', 'init.sql')
        if os.path.exists(init_sql_path):
            with open(init_sql_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            # 分割SQL语句并执行
            with engine.connect() as conn:
                # 只执行插入默认分类的部分
                insert_categories_sql = """
                INSERT INTO bill_categories (family_id, category_name, color, icon) VALUES 
                (NULL, '食品酒饮', '#FF6B6B', 'food'),
                (NULL, '服饰内衣', '#4ECDC4', 'clothing'),
                (NULL, '日用百货', '#45B7D1', 'daily'),
                (NULL, '数码电器', '#96CEB4', 'digital'),
                (NULL, '交通出行', '#FFEAA7', 'transport'),
                (NULL, '医疗保健', '#DDA0DD', 'medical'),
                (NULL, '教育培训', '#98D8C8', 'education'),
                (NULL, '运动户外', '#F7DC6F', 'sports'),
                (NULL, '住房物业', '#BB8FCE', 'housing'),
                (NULL, '投资理财', '#85C1E9', 'investment'),
                (NULL, '转账红包', '#F8C471', 'transfer'),
                (NULL, '其他', '#D5DBDB', 'other')
                ON CONFLICT (family_id, category_name) DO NOTHING;
                """
                
                try:
                    conn.execute(text(insert_categories_sql))
                    conn.commit()
                    print("默认分类插入成功！")
                except Exception as e:
                    print(f"插入默认分类时出错（可能已存在）: {e}")
        
        return True
    except Exception as e:
        print(f"运行初始化SQL失败: {e}")
        return False

def main():
    """
    主函数
    """
    print("PostgreSQL数据库设置脚本")
    print("=" * 40)
    
    # 检查环境变量
    if not settings.DATABASE_URL.startswith('postgresql://'):
        print("错误：请在.env文件中设置正确的PostgreSQL DATABASE_URL")
        print("示例：DATABASE_URL=postgresql://postgres:password@localhost:5432/bills_db")
        sys.exit(1)
    
    print(f"数据库URL: {settings.DATABASE_URL}")
    
    # 步骤1：创建数据库
    if not create_database():
        print("数据库创建失败，请检查PostgreSQL服务是否运行以及连接信息是否正确")
        sys.exit(1)
    
    # 步骤2：创建表
    if not create_tables():
        print("表创建失败")
        sys.exit(1)
    
    # 步骤3：运行初始化SQL
    if not run_init_sql():
        print("初始化SQL运行失败")
        sys.exit(1)
    
    print("\n" + "=" * 40)
    print("PostgreSQL数据库设置完成！")
    print("现在可以启动应用程序了")

if __name__ == "__main__":
    main()