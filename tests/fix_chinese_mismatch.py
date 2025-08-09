#!/usr/bin/env python3
"""
修复中文字段的分类不匹配问题
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def fix_chinese_mismatch():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查找所有不匹配的记录（使用中文字段）
        print("=== 查找不匹配的记录 ===")
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
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE (b.transaction_type = '收入' AND bc.category_type = 'expense')
        OR (b.transaction_type = '支出' AND bc.category_type = 'income')
        ORDER BY b.id
        """)
        
        mismatch_records = cursor.fetchall()
        
        print(f"找到 {len(mismatch_records)} 条不匹配记录:")
        
        if not mismatch_records:
            print("✅ 没有发现不匹配的记录")
            return
        
        print("-" * 100)
        print(f"{'ID':<6} {'交易类型':<8} {'金额':<10} {'分类名称':<15} {'分类类型':<10} {'描述':<30}")
        print("-" * 100)
        
        for record in mismatch_records:
            print(f"{record['id']:<6} {record['transaction_type']:<8} {record['amount']:<10} "
                  f"{record['category_name']:<15} {record['category_type']:<10} "
                  f"{(record['transaction_desc'] or '')[:28]:<30}")
        
        # 获取正确的分类ID
        cursor.execute("SELECT id FROM bill_categories WHERE category_name = '投资收益'")
        investment_income = cursor.fetchone()
        
        cursor.execute("SELECT id FROM bill_categories WHERE category_name = '理财投资'")
        investment_expense = cursor.fetchone()
        
        cursor.execute("SELECT id FROM bill_categories WHERE category_name = '其他收入'")
        other_income = cursor.fetchone()
        
        cursor.execute("SELECT id FROM bill_categories WHERE category_name = '其他支出'")
        other_expense = cursor.fetchone()
        
        print(f"\n可用的分类:")
        print(f"  投资收益 (收入): {investment_income['id'] if investment_income else 'Not Found'}")
        print(f"  理财投资 (支出): {investment_expense['id'] if investment_expense else 'Not Found'}")
        print(f"  其他收入: {other_income['id'] if other_income else 'Not Found'}")
        print(f"  其他支出: {other_expense['id'] if other_expense else 'Not Found'}")
        
        # 修复记录
        print(f"\n=== 开始修复 ===")
        fixed_count = 0
        
        for record in mismatch_records:
            bill_id = record['id']
            transaction_type = record['transaction_type']
            transaction_desc = record['transaction_desc'] or ""
            current_category_type = record['category_type']
            
            new_category_id = None
            new_category_name = ""
            
            if transaction_type == '收入' and current_category_type == 'expense':
                # 收入类型但使用了支出分类
                if "基金" in transaction_desc or "理财" in transaction_desc or "赎回" in transaction_desc:
                    new_category_id = investment_income['id'] if investment_income else None
                    new_category_name = "投资收益"
                else:
                    new_category_id = other_income['id'] if other_income else None
                    new_category_name = "其他收入"
            
            elif transaction_type == '支出' and current_category_type == 'income':
                # 支出类型但使用了收入分类
                if "基金" in transaction_desc or "理财" in transaction_desc or "投资" in transaction_desc:
                    new_category_id = investment_expense['id'] if investment_expense else None
                    new_category_name = "理财投资"
                else:
                    new_category_id = other_expense['id'] if other_expense else None
                    new_category_name = "其他支出"
            
            if new_category_id:
                print(f"修复账单 {bill_id}:")
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
                print()
        
        # 提交更改
        if fixed_count > 0:
            conn.commit()
            print(f"=== 修复完成 ===")
            print(f"总共修复了 {fixed_count} 条记录")
        
        # 最终验证
        print(f"\n=== 最终验证 ===")
        cursor.execute("""
        SELECT 
            COUNT(*) as count
        FROM bills b
        JOIN bill_categories bc ON b.category_id = bc.id
        WHERE (b.transaction_type = '收入' AND bc.category_type = 'expense')
        OR (b.transaction_type = '支出' AND bc.category_type = 'income')
        """)
        
        remaining_count = cursor.fetchone()['count']
        
        if remaining_count > 0:
            print(f"⚠️  仍有 {remaining_count} 条记录存在问题")
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
    fix_chinese_mismatch()