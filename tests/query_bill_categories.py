#!/usr/bin/env python3
"""
查询 bill_categories 表的脚本
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def query_bill_categories():
    """查询账单分类表"""
    
    # 数据库连接信息
    DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"
    
    try:
        # 连接数据库
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询 bill_categories 表结构
        print("\n=== 查询表结构 ===")
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'bill_categories'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        if columns:
            print("表结构:")
            for col in columns:
                print(f"  - {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
                if col['column_default']:
                    print(f"    默认值: {col['column_default']}")
        else:
            print("未找到 bill_categories 表")
            return
        
        # 查询所有分类数据
        print("\n=== 查询分类数据 ===")
        cursor.execute("""
            SELECT id, category_name, description, parent_id, created_at, category_type, color, icon
            FROM bill_categories 
            ORDER BY parent_id NULLS FIRST, id;
        """)
        
        categories = cursor.fetchall()
        
        if categories:
            print(f"共找到 {len(categories)} 个分类:")
            print()
            
            # 分组显示：先显示顶级分类，再显示子分类
            top_level = [cat for cat in categories if cat['parent_id'] is None]
            sub_level = [cat for cat in categories if cat['parent_id'] is not None]
            
            print("📁 顶级分类:")
            for cat in top_level:
                print(f"  {cat['id']}. {cat['category_name']}")
                if cat['description']:
                    print(f"     描述: {cat['description']}")
                print(f"     类型: {cat['category_type']}")
                if cat['color']:
                    print(f"     颜色: {cat['color']}")
                if cat['icon']:
                    print(f"     图标: {cat['icon']}")
                print(f"     创建时间: {cat['created_at']}")
                print()
            
            if sub_level:
                print("📂 子分类:")
                for cat in sub_level:
                    parent_name = next((p['category_name'] for p in categories if p['id'] == cat['parent_id']), '未知')
                    print(f"  {cat['id']}. {cat['category_name']} (父分类: {parent_name})")
                    if cat['description']:
                        print(f"     描述: {cat['description']}")
                    print(f"     类型: {cat['category_type']}")
                    if cat['color']:
                        print(f"     颜色: {cat['color']}")
                    if cat['icon']:
                        print(f"     图标: {cat['icon']}")
                    print(f"     创建时间: {cat['created_at']}")
                    print()
        else:
            print("表中没有数据")
        
        # 统计信息
        print("=== 统计信息 ===")
        cursor.execute("SELECT COUNT(*) as total FROM bill_categories")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as top_level FROM bill_categories WHERE parent_id IS NULL")
        top_level_count = cursor.fetchone()['top_level']
        
        cursor.execute("SELECT COUNT(*) as sub_level FROM bill_categories WHERE parent_id IS NOT NULL")
        sub_level_count = cursor.fetchone()['sub_level']
        
        print(f"总分类数: {total}")
        print(f"顶级分类: {top_level_count}")
        print(f"子分类: {sub_level_count}")
        
    except psycopg2.Error as e:
        print(f"数据库错误: {e}")
    except Exception as e:
        print(f"其他错误: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()
        print("\n数据库连接已关闭")

if __name__ == "__main__":
    query_bill_categories()