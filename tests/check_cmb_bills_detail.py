#!/usr/bin/env python3
"""
检查 CMB 导入的账单详情
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def check_cmb_bills():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查询所有CMB账单
        query = """
        SELECT 
            b.id,
            b.transaction_type,
            b.amount,
            b.transaction_desc,
            b.category_id,
            bc.category_name,
            bc.category_type,
            b.source_type,
            b.transaction_time,
            b.counter_party
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.source_type = 'cmb'
        ORDER BY b.transaction_time DESC;
        """
        
        cursor.execute(query)
        cmb_bills = cursor.fetchall()
        
        print(f"\n=== CMB 账单总数: {len(cmb_bills)} 条 ===")
        
        if cmb_bills:
            print("\nCMB 账单详情:")
            print("-" * 140)
            print(f"{'ID':<6} {'类型':<8} {'金额':<12} {'分类ID':<8} {'分类名称':<15} {'分类类型':<10} {'描述':<25} {'交易对方':<20}")
            print("-" * 140)
            
            income_count = 0
            expense_count = 0
            
            for bill in cmb_bills:
                if bill['transaction_type'] == 'income':
                    income_count += 1
                else:
                    expense_count += 1
                    
                print(f"{bill['id']:<6} {bill['transaction_type']:<8} {bill['amount']:<12.2f} "
                      f"{bill['category_id'] or 'NULL':<8} {(bill['category_name'] or '未分类'):<15} "
                      f"{(bill['category_type'] or 'N/A'):<10} {(bill['transaction_desc'] or '')[:23]:<25} "
                      f"{(bill['counter_party'] or '')[:18]:<20}")
        
            print(f"\n统计:")
            print(f"收入账单: {income_count} 条")
            print(f"支出账单: {expense_count} 条")
            
            # 检查是否有不匹配的情况
            mismatched = []
            for bill in cmb_bills:
                if bill['category_id'] and bill['category_type']:
                    if (bill['transaction_type'] == 'income' and bill['category_type'] == 'expense') or \
                       (bill['transaction_type'] == 'expense' and bill['category_type'] == 'income'):
                        mismatched.append(bill)
            
            if mismatched:
                print(f"\n⚠️  发现 {len(mismatched)} 条不匹配的记录:")
                for bill in mismatched:
                    print(f"  账单ID {bill['id']}: {bill['transaction_type']} 类型使用了 {bill['category_type']} 分类 ({bill['category_name']})")
            else:
                print("\n✅ 所有CMB账单的分类匹配正确")
        
        # 查看最近的一些账单，看看自动分类的情况
        print(f"\n=== 最近的账单分类情况 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.amount,
            b.transaction_desc,
            b.category_id,
            bc.category_name,
            bc.category_type,
            b.source_type
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        ORDER BY b.id DESC
        LIMIT 20;
        """)
        
        recent_bills = cursor.fetchall()
        
        print(f"最近20条账单:")
        print("-" * 120)
        print(f"{'ID':<6} {'类型':<8} {'金额':<12} {'分类':<15} {'分类类型':<10} {'描述':<25} {'来源':<8}")
        print("-" * 120)
        
        for bill in recent_bills:
            print(f"{bill['id']:<6} {bill['transaction_type']:<8} {bill['amount']:<12.2f} "
                  f"{(bill['category_name'] or '未分类'):<15} {(bill['category_type'] or 'N/A'):<10} "
                  f"{(bill['transaction_desc'] or '')[:23]:<25} {bill['source_type']:<8}")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")

if __name__ == "__main__":
    check_cmb_bills()