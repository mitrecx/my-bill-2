#!/usr/bin/env python3
"""
检查 bills 表中 category_id 和 transaction_type 的匹配情况
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def check_category_mismatch():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询不匹配的记录
        query = """
        SELECT 
            b.id as bill_id,
            b.transaction_type,
            b.category_id,
            bc.category_name,
            bc.category_type,
            b.transaction_desc,
            b.amount,
            b.source_type
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.category_id IS NOT NULL 
        AND (
            (b.transaction_type = 'income' AND bc.category_type = 'expense') OR
            (b.transaction_type = 'expense' AND bc.category_type = 'income')
        )
        ORDER BY b.id;
        """
        
        cursor.execute(query)
        mismatched_records = cursor.fetchall()
        
        print(f"\n=== 发现 {len(mismatched_records)} 条不匹配的记录 ===")
        
        if mismatched_records:
            print("\n不匹配的记录详情:")
            print("-" * 120)
            print(f"{'账单ID':<8} {'交易类型':<10} {'分类ID':<8} {'分类名称':<15} {'分类类型':<10} {'金额':<12} {'描述':<20} {'来源':<8}")
            print("-" * 120)
            
            for record in mismatched_records:
                print(f"{record['bill_id']:<8} {record['transaction_type']:<10} {record['category_id']:<8} "
                      f"{record['category_name']:<15} {record['category_type']:<10} {record['amount']:<12.2f} "
                      f"{(record['transaction_desc'] or '')[:18]:<20} {record['source_type']:<8}")
        
        # 统计各种情况
        print(f"\n=== 统计信息 ===")
        
        # 收入账单使用支出分类的情况
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.transaction_type = 'income' AND bc.category_type = 'expense'
        """)
        income_with_expense_cat = cursor.fetchone()['count']
        
        # 支出账单使用收入分类的情况
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.transaction_type = 'expense' AND bc.category_type = 'income'
        """)
        expense_with_income_cat = cursor.fetchone()['count']
        
        print(f"收入账单使用支出分类: {income_with_expense_cat} 条")
        print(f"支出账单使用收入分类: {expense_with_income_cat} 条")
        
        # 查看分类分布
        print(f"\n=== 分类分布 ===")
        cursor.execute("""
        SELECT 
            bc.category_type,
            bc.category_name,
            COUNT(b.id) as bill_count
        FROM bill_categories bc
        LEFT JOIN bills b ON bc.id = b.category_id
        GROUP BY bc.id, bc.category_type, bc.category_name
        ORDER BY bc.category_type, bc.category_name
        """)
        
        category_stats = cursor.fetchall()
        
        current_type = None
        for stat in category_stats:
            if stat['category_type'] != current_type:
                current_type = stat['category_type']
                print(f"\n{current_type.upper()} 分类:")
                print("-" * 40)
            print(f"  {stat['category_name']:<20} {stat['bill_count']} 条账单")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_category_mismatch()