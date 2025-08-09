#!/usr/bin/env python3
"""
查看账单分类数据 - 按类型分组显示
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def main():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询收入分类
        print("\n" + "="*50)
        print("💰 收入分类")
        print("="*50)
        cursor.execute("""
            SELECT id, category_name, description, color, icon
            FROM bill_categories 
            WHERE category_type = 'income'
            ORDER BY category_name
        """)
        income_categories = cursor.fetchall()
        
        for i, cat in enumerate(income_categories, 1):
            print(f"{i:2d}. {cat['category_name']}")
            print(f"    描述: {cat['description']}")
            print(f"    颜色: {cat['color']}")
            print(f"    图标: {cat['icon']}")
            print()
        
        # 查询支出分类
        print("="*50)
        print("💸 支出分类")
        print("="*50)
        cursor.execute("""
            SELECT id, category_name, description, color, icon
            FROM bill_categories 
            WHERE category_type = 'expense'
            ORDER BY category_name
        """)
        expense_categories = cursor.fetchall()
        
        for i, cat in enumerate(expense_categories, 1):
            print(f"{i:2d}. {cat['category_name']}")
            print(f"    描述: {cat['description']}")
            print(f"    颜色: {cat['color']}")
            print(f"    图标: {cat['icon']}")
            print()
        
        # 统计信息
        print("="*50)
        print("📊 统计信息")
        print("="*50)
        print(f"收入分类: {len(income_categories)} 个")
        print(f"支出分类: {len(expense_categories)} 个")
        print(f"总计: {len(income_categories) + len(expense_categories)} 个分类")
        
        cursor.close()
        conn.close()
        print("\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main()