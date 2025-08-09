#!/usr/bin/env python3
"""
修复具体的分类不匹配问题
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def fix_specific_mismatches():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查找具体的问题记录
        print("=== 查找具体的问题记录 ===")
        
        # 查找收入类型但使用支出分类的记录
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
        OR (b.transaction_type = 'income' AND bc.category_type = 'expense')
        OR (b.transaction_type = 'expense' AND bc.category_type = 'income')
        ORDER BY b.id DESC
        """)
        
        problem_records = cursor.fetchall()
        
        print(f"找到 {len(problem_records)} 条问题记录:")
        print("-" * 100)
        print(f"{'ID':<6} {'类型':<8} {'分类ID':<8} {'分类名称':<15} {'分类类型':<10} {'描述':<30}")
        print("-" * 100)
        
        for record in problem_records:
            print(f"{record['id']:<6} {record['transaction_type']:<8} {record['category_id']:<8} "
                  f"{(record['category_name'] or '未分类'):<15} {(record['category_type'] or 'N/A'):<10} "
                  f"{(record['transaction_desc'] or '')[:28]:<30}")
        
        # 获取正确的分类ID
        cursor.execute("SELECT id, category_name FROM bill_categories WHERE category_name = '投资收益'")
        investment_income_cat = cursor.fetchone()
        
        cursor.execute("SELECT id, category_name FROM bill_categories WHERE category_name = '理财投资'")
        investment_expense_cat = cursor.fetchone()
        
        print(f"\n投资收益分类ID: {investment_income_cat['id'] if investment_income_cat else 'Not Found'}")
        print(f"理财投资分类ID: {investment_expense_cat['id'] if investment_expense_cat else 'Not Found'}")
        
        # 修复具体的问题记录
        fixed_count = 0
        
        for record in problem_records:
            bill_id = record['id']
            transaction_type = record['transaction_type']
            transaction_desc = record['transaction_desc'] or ""
            current_category_type = record['category_type']
            
            # 检查是否需要修复
            needs_fix = False
            new_category_id = None
            new_category_name = ""
            
            if transaction_type == 'income' and current_category_type == 'expense':
                needs_fix = True
                if "基金" in transaction_desc or "理财" in transaction_desc:
                    new_category_id = investment_income_cat['id'] if investment_income_cat else None
                    new_category_name = "投资收益"
                else:
                    # 其他收入类型的错误分类，设为其他收入
                    cursor.execute("SELECT id FROM bill_categories WHERE category_name = '其他收入'")
                    other_income = cursor.fetchone()
                    new_category_id = other_income['id'] if other_income else None
                    new_category_name = "其他收入"
            
            elif transaction_type == 'expense' and current_category_type == 'income':
                needs_fix = True
                if "基金" in transaction_desc or "理财" in transaction_desc:
                    new_category_id = investment_expense_cat['id'] if investment_expense_cat else None
                    new_category_name = "理财投资"
                else:
                    # 其他支出类型的错误分类，设为其他支出
                    cursor.execute("SELECT id FROM bill_categories WHERE category_name = '其他支出'")
                    other_expense = cursor.fetchone()
                    new_category_id = other_expense['id'] if other_expense else None
                    new_category_name = "其他支出"
            
            if needs_fix and new_category_id:
                print(f"\n修复账单 {bill_id}:")
                print(f"  描述: {transaction_desc}")
                print(f"  类型: {transaction_type}")
                print(f"  原分类: {record['category_name']} ({current_category_type})")
                print(f"  新分类: {new_category_name}")
                
                cursor.execute("""
                UPDATE bills 
                SET category_id = %s 
                WHERE id = %s
                """, (new_category_id, bill_id))
                
                fixed_count += 1
                print(f"  ✅ 已修复")
        
        # 提交更改
        if fixed_count > 0:
            conn.commit()
            print(f"\n=== 修复完成 ===")
            print(f"总共修复了 {fixed_count} 条记录")
        else:
            print(f"\n=== 无需修复 ===")
            print("没有发现需要修复的记录")
        
        # 最终验证
        print(f"\n=== 最终验证 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.transaction_desc,
            bc.category_name,
            bc.category_type
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE (b.transaction_type = 'income' AND bc.category_type = 'expense')
        OR (b.transaction_type = 'expense' AND bc.category_type = 'income')
        """)
        
        remaining_issues = cursor.fetchall()
        
        if remaining_issues:
            print(f"⚠️  仍有 {len(remaining_issues)} 条记录存在问题:")
            for issue in remaining_issues:
                print(f"  账单 {issue['id']}: {issue['transaction_type']} 使用 {issue['category_type']} 分类")
        else:
            print("✅ 所有分类匹配问题已解决")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    fix_specific_mismatches()