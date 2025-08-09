#!/usr/bin/env python3
"""
修复基金赎回的分类问题
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def fix_fund_redemption():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 获取投资收益分类ID
        cursor.execute("SELECT id FROM bill_categories WHERE category_name = '投资收益'")
        investment_income_cat = cursor.fetchone()
        
        if not investment_income_cat:
            print("错误: 找不到'投资收益'分类")
            return
        
        investment_income_id = investment_income_cat['id']
        print(f"投资收益分类ID: {investment_income_id}")
        
        # 查找需要修复的记录
        print("\n=== 查找需要修复的记录 ===")
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
        AND b.transaction_desc LIKE '%基金赎回%'
        """)
        
        problem_records = cursor.fetchall()
        
        print(f"找到 {len(problem_records)} 条需要修复的基金赎回记录:")
        
        if not problem_records:
            print("没有找到需要修复的记录")
            return
        
        print("-" * 80)
        print(f"{'ID':<6} {'金额':<10} {'原分类':<15} {'描述':<30}")
        print("-" * 80)
        
        for record in problem_records:
            print(f"{record['id']:<6} {record['amount']:<10} "
                  f"{(record['category_name'] or '未分类'):<15} "
                  f"{(record['transaction_desc'] or '')[:28]:<30}")
        
        # 执行修复
        print(f"\n=== 开始修复 ===")
        
        for record in problem_records:
            bill_id = record['id']
            print(f"修复账单 {bill_id}: {record['transaction_desc']}")
            
            cursor.execute("""
            UPDATE bills 
            SET category_id = %s 
            WHERE id = %s
            """, (investment_income_id, bill_id))
            
            print(f"  ✅ 已将分类从 '{record['category_name']}' 改为 '投资收益'")
        
        # 提交更改
        conn.commit()
        print(f"\n=== 修复完成 ===")
        print(f"总共修复了 {len(problem_records)} 条记录")
        
        # 验证修复结果
        print(f"\n=== 验证修复结果 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.transaction_desc,
            bc.category_name,
            bc.category_type
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.transaction_type = 'income' 
        AND bc.category_type = 'expense'
        """)
        
        remaining_issues = cursor.fetchall()
        
        if remaining_issues:
            print(f"⚠️  仍有 {len(remaining_issues)} 条收入记录使用支出分类:")
            for issue in remaining_issues:
                print(f"  账单 {issue['id']}: {issue['transaction_desc']} -> {issue['category_name']}")
        else:
            print("✅ 所有收入记录的分类问题已解决")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    fix_fund_redemption()