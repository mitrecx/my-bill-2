#!/usr/bin/env python3
"""
检查具体的账单记录
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def check_specific_bills():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询具体的账单记录
        print("=== 查询账单 10753 和 10745 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.transaction_desc,
            b.amount,
            b.category_id,
            bc.category_name,
            bc.category_type
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.id IN (10753, 10745)
        ORDER BY b.id
        """)
        
        records = cursor.fetchall()
        
        print(f"找到 {len(records)} 条记录:")
        print("-" * 100)
        print(f"{'ID':<6} {'类型':<8} {'金额':<10} {'分类ID':<8} {'分类名称':<15} {'分类类型':<10} {'描述':<30}")
        print("-" * 100)
        
        for record in records:
            print(f"{record['id']:<6} {record['transaction_type']:<8} {record['amount']:<10} "
                  f"{record['category_id']:<8} {(record['category_name'] or '未分类'):<15} "
                  f"{(record['category_type'] or 'N/A'):<10} "
                  f"{(record['transaction_desc'] or '')[:28]:<30}")
        
        # 查询所有收入类型但使用支出分类的记录
        print("\n=== 查询所有收入类型但使用支出分类的记录 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.transaction_desc,
            b.amount,
            b.category_id,
            bc.category_name,
            bc.category_type
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.transaction_type = 'income' 
        AND bc.category_type = 'expense'
        ORDER BY b.id
        """)
        
        mismatch_records = cursor.fetchall()
        
        print(f"找到 {len(mismatch_records)} 条不匹配记录:")
        
        if mismatch_records:
            print("-" * 100)
            print(f"{'ID':<6} {'类型':<8} {'金额':<10} {'分类ID':<8} {'分类名称':<15} {'分类类型':<10} {'描述':<30}")
            print("-" * 100)
            
            for record in mismatch_records:
                print(f"{record['id']:<6} {record['transaction_type']:<8} {record['amount']:<10} "
                      f"{record['category_id']:<8} {(record['category_name'] or '未分类'):<15} "
                      f"{(record['category_type'] or 'N/A'):<10} "
                      f"{(record['transaction_desc'] or '')[:28]:<30}")
        
        # 获取投资收益分类ID
        cursor.execute("SELECT id, category_name, category_type FROM bill_categories WHERE category_name = '投资收益'")
        investment_income = cursor.fetchone()
        
        print(f"\n投资收益分类: ID={investment_income['id']}, 类型={investment_income['category_type']}")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_specific_bills()