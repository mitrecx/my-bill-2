#!/usr/bin/env python3
"""
检查和修复包含"信雅达"的CMB账单记录
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

def fix_xinyada_bills():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查找包含"信雅达"的账单记录
        print("=== 查找包含'信雅达'的账单记录 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.transaction_desc,
            b.amount,
            b.counter_party,
            b.category_id,
            bc.category_name,
            bc.category_type,
            b.source_type
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.counter_party LIKE '%信雅达%'
        ORDER BY b.id DESC
        """)
        
        xinyada_records = cursor.fetchall()
        
        print(f"找到 {len(xinyada_records)} 条包含'信雅达'的记录:")
        
        if not xinyada_records:
            print("没有找到包含'信雅达'的记录")
            return
        
        print("-" * 120)
        print(f"{'ID':<6} {'类型':<8} {'金额':<10} {'分类名称':<15} {'分类类型':<10} {'对手方':<20} {'来源':<8} {'描述':<20}")
        print("-" * 120)
        
        for record in xinyada_records:
            print(f"{record['id']:<6} {record['transaction_type']:<8} {record['amount']:<10} "
                  f"{(record['category_name'] or '未分类'):<15} {(record['category_type'] or 'N/A'):<10} "
                  f"{(record['counter_party'] or '')[:18]:<20} {record['source_type']:<8} "
                  f"{(record['transaction_desc'] or '')[:18]:<20}")
        
        # 获取工资收入分类ID
        cursor.execute("SELECT id FROM bill_categories WHERE category_name = '工资收入'")
        salary_category = cursor.fetchone()
        
        if not salary_category:
            print("错误: 找不到'工资收入'分类")
            return
        
        salary_category_id = salary_category['id']
        print(f"\n工资收入分类ID: {salary_category_id}")
        
        # 筛选需要修复的记录（收入类型且不是工资收入分类的）
        need_fix_records = []
        for record in xinyada_records:
            if (record['transaction_type'] == '收入' and 
                record['category_name'] != '工资收入'):
                need_fix_records.append(record)
        
        print(f"\n=== 需要修复的记录 ===")
        print(f"找到 {len(need_fix_records)} 条需要修复的记录:")
        
        if not need_fix_records:
            print("所有包含'信雅达'的收入记录已经正确分类为'工资收入'")
            return
        
        for record in need_fix_records:
            print(f"账单 {record['id']}: {record['transaction_type']} - "
                  f"当前分类: {record['category_name'] or '未分类'} -> 应改为: 工资收入")
        
        # 执行修复
        print(f"\n=== 开始修复 ===")
        
        for record in need_fix_records:
            bill_id = record['id']
            print(f"修复账单 {bill_id}:")
            print(f"  对手方: {record['counter_party']}")
            print(f"  描述: {record['transaction_desc']}")
            print(f"  类型: {record['transaction_type']}")
            print(f"  原分类: {record['category_name'] or '未分类'}")
            print(f"  新分类: 工资收入")
            
            cursor.execute("""
            UPDATE bills 
            SET category_id = %s 
            WHERE id = %s
            """, (salary_category_id, bill_id))
            
            print(f"  ✅ 已修复")
            print()
        
        # 提交更改
        if need_fix_records:
            conn.commit()
            print(f"=== 修复完成 ===")
            print(f"总共修复了 {len(need_fix_records)} 条记录")
        
        # 最终验证
        print(f"\n=== 最终验证 ===")
        cursor.execute("""
        SELECT 
            b.id,
            b.transaction_type,
            b.counter_party,
            bc.category_name
        FROM bills b
        LEFT JOIN bill_categories bc ON b.category_id = bc.id
        WHERE b.counter_party LIKE '%信雅达%'
        AND b.transaction_type = '收入'
        ORDER BY b.id DESC
        """)
        
        final_records = cursor.fetchall()
        
        print("修复后的'信雅达'收入记录:")
        for record in final_records:
            status = "✅ 正确" if record['category_name'] == '工资收入' else "❌ 错误"
            print(f"  账单 {record['id']}: {record['category_name']} {status}")
        
        cursor.close()
        conn.close()
        print(f"\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")
        if 'conn' in locals():
            conn.rollback()

if __name__ == "__main__":
    fix_xinyada_bills()