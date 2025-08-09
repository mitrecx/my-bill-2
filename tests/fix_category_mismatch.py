#!/usr/bin/env python3
"""
修复 bills 表中 category_id 和 transaction_type 不匹配的问题
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def fix_category_mismatch():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 首先获取所有分类的映射
        cursor.execute("""
        SELECT id, category_name, category_type 
        FROM bill_categories 
        ORDER BY category_type, category_name
        """)
        categories = cursor.fetchall()
        
        print("=== 当前分类列表 ===")
        income_categories = {}
        expense_categories = {}
        
        for cat in categories:
            if cat['category_type'] == 'income':
                income_categories[cat['category_name']] = cat['id']
                print(f"收入分类: {cat['id']} - {cat['category_name']}")
            else:
                expense_categories[cat['category_name']] = cat['id']
                print(f"支出分类: {cat['id']} - {cat['category_name']}")
        
        # 查找需要修复的记录
        print(f"\n=== 查找需要修复的记录 ===")
        
        # 1. 收入类型使用支出分类的记录
        cursor.execute("""
        SELECT 
            b.id, b.transaction_desc, b.amount, bc.category_name, bc.category_type
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.transaction_type = 'income' AND bc.category_type = 'expense'
        """)
        income_with_expense_cat = cursor.fetchall()
        
        # 2. 支出类型使用收入分类的记录
        cursor.execute("""
        SELECT 
            b.id, b.transaction_desc, b.amount, bc.category_name, bc.category_type
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.transaction_type = 'expense' AND bc.category_type = 'income'
        """)
        expense_with_income_cat = cursor.fetchall()
        
        print(f"收入账单使用支出分类: {len(income_with_expense_cat)} 条")
        print(f"支出账单使用收入分类: {len(expense_with_income_cat)} 条")
        
        # 修复收入账单的分类
        fixed_count = 0
        
        if income_with_expense_cat:
            print(f"\n=== 修复收入账单的分类 ===")
            for record in income_with_expense_cat:
                bill_id = record['id']
                desc = record['transaction_desc'] or ""
                current_category = record['category_name']
                
                # 根据描述确定正确的收入分类
                new_category_id = None
                new_category_name = ""
                
                if "基金" in desc or "理财" in desc:
                    new_category_id = income_categories.get("投资收益")
                    new_category_name = "投资收益"
                elif "工资" in desc or "奖金" in desc:
                    new_category_id = income_categories.get("工资收入")
                    new_category_name = "工资收入"
                elif "退款" in desc:
                    new_category_id = income_categories.get("退款收入")
                    new_category_name = "退款收入"
                elif "红包" in desc or "鼓励金" in desc:
                    new_category_id = income_categories.get("红包")
                    new_category_name = "红包"
                else:
                    new_category_id = income_categories.get("其他收入")
                    new_category_name = "其他收入"
                
                if new_category_id:
                    cursor.execute("""
                    UPDATE bills 
                    SET category_id = %s 
                    WHERE id = %s
                    """, (new_category_id, bill_id))
                    
                    print(f"  账单 {bill_id}: {desc[:30]} | {current_category} -> {new_category_name}")
                    fixed_count += 1
                else:
                    print(f"  ⚠️  账单 {bill_id}: 无法找到合适的收入分类")
        
        # 修复支出账单的分类
        if expense_with_income_cat:
            print(f"\n=== 修复支出账单的分类 ===")
            for record in expense_with_income_cat:
                bill_id = record['id']
                desc = record['transaction_desc'] or ""
                current_category = record['category_name']
                
                # 根据描述确定正确的支出分类
                new_category_id = None
                new_category_name = ""
                
                if "基金" in desc or "理财" in desc:
                    new_category_id = expense_categories.get("理财投资")
                    new_category_name = "理财投资"
                elif "还款" in desc:
                    new_category_id = expense_categories.get("还款")
                    new_category_name = "还款"
                else:
                    new_category_id = expense_categories.get("其他支出")
                    new_category_name = "其他支出"
                
                if new_category_id:
                    cursor.execute("""
                    UPDATE bills 
                    SET category_id = %s 
                    WHERE id = %s
                    """, (new_category_id, bill_id))
                    
                    print(f"  账单 {bill_id}: {desc[:30]} | {current_category} -> {new_category_name}")
                    fixed_count += 1
                else:
                    print(f"  ⚠️  账单 {bill_id}: 无法找到合适的支出分类")
        
        # 提交更改
        conn.commit()
        
        print(f"\n=== 修复完成 ===")
        print(f"总共修复了 {fixed_count} 条记录")
        
        # 验证修复结果
        print(f"\n=== 验证修复结果 ===")
        cursor.execute("""
        SELECT COUNT(*) as count
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE (b.transaction_type = 'income' AND bc.category_type = 'expense') OR
              (b.transaction_type = 'expense' AND bc.category_type = 'income')
        """)
        remaining_mismatches = cursor.fetchone()['count']
        
        if remaining_mismatches == 0:
            print("✅ 所有分类不匹配问题已修复")
        else:
            print(f"⚠️  仍有 {remaining_mismatches} 条记录存在分类不匹配问题")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    fix_category_mismatch()