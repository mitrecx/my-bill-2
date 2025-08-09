#!/usr/bin/env python3
"""
检查数据类型问题
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def check_data_types():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询具体记录并检查数据类型
        print("=== 检查数据类型 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.transaction_desc,
            b.category_id,
            bc.category_name,
            bc.category_type
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.id IN (10753, 10745)
        """)
        
        records = cursor.fetchall()
        
        for record in records:
            print(f"账单ID: {record['id']}")
            print(f"  transaction_type: '{record['transaction_type']}' (type: {type(record['transaction_type'])})")
            print(f"  category_type: '{record['category_type']}' (type: {type(record['category_type'])})")
            
            # 检查字符串内容
            trans_type = record['transaction_type']
            cat_type = record['category_type']
            
            print(f"  transaction_type == 'income': {trans_type == 'income'}")
            print(f"  category_type == 'expense': {cat_type == 'expense'}")
            print(f"  是否不匹配: {trans_type == 'income' and cat_type == 'expense'}")
            
            # 检查是否有隐藏字符
            print(f"  transaction_type repr: {repr(trans_type)}")
            print(f"  category_type repr: {repr(cat_type)}")
            print()
        
        # 现在检查修复后的状态
        print("=== 检查修复后的状态 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.transaction_desc,
            b.category_id,
            bc.category_name,
            bc.category_type
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.id IN (10753, 10745)
        """)
        
        fixed_records = cursor.fetchall()
        
        for record in fixed_records:
            print(f"账单ID: {record['id']}")
            print(f"  交易类型: {record['transaction_type']}")
            print(f"  分类名称: {record['category_name']}")
            print(f"  分类类型: {record['category_type']}")
            
            trans_type = record['transaction_type'].strip()
            cat_type = record['category_type'].strip()
            
            is_correct = (trans_type == 'income' and cat_type == 'income') or (trans_type == 'expense' and cat_type == 'expense')
            print(f"  匹配状态: {'✅ 正确' if is_correct else '❌ 错误'}")
            print()
        
        # 最终验证：查找所有不匹配的记录
        print("=== 最终验证：查找所有不匹配的记录 ===")
        cursor.execute("""
        SELECT 
            COUNT(*) as count,
            b.transaction_type,
            bc.category_type
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE (b.transaction_type = 'income' AND bc.category_type = 'expense')
        OR (b.transaction_type = 'expense' AND bc.category_type = 'income')
        GROUP BY b.transaction_type, bc.category_type
        """)
        
        mismatch_summary = cursor.fetchall()
        
        if mismatch_summary:
            print("发现不匹配记录:")
            for summary in mismatch_summary:
                print(f"  {summary['transaction_type']} 类型使用 {summary['category_type']} 分类: {summary['count']} 条")
        else:
            print("✅ 没有发现不匹配的记录")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_data_types()