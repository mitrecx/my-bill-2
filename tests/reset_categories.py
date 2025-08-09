#!/usr/bin/env python3
"""
根据账单分类体系.md重新插入分类数据
确保ID从1开始
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('backend/config/environments/development.env')

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

# 根据账单分类体系.md定义的分类数据
CATEGORIES = [
    # 收入分类（7个）
    ('工资收入', '#52C41A', 'salary', 'income', '工资、奖金等'),
    ('投资收益', '#1890FF', 'investment', 'income', '股票、基金、理财等'),
    ('兼职收入', '#722ED1', 'parttime', 'income', '副业、兼职等'),
    ('借款', '#FA8C16', 'loan', 'income', '向他人借款'),
    ('退款收入', '#13C2C2', 'refund', 'income', '各种退款'),
    ('红包', '#F5222D', 'redpacket', 'income', '红包、礼金等'),
    ('其他收入', '#8C8C8C', 'other', 'income', '其他收入来源'),
    
    # 支出分类（13个）
    ('食品餐饮', '#FF6B6B', 'food', 'expense', '餐饮、零食等'),
    ('服饰鞋包', '#4ECDC4', 'clothing', 'expense', '衣服、鞋子、包包等'),
    ('美妆个护', '#FF69B4', 'beauty', 'expense', '化妆品、护肤品等'),
    ('日用百货', '#45B7D1', 'daily', 'expense', '日常用品、家具、家电等'),
    ('交通出行', '#FFEAA7', 'transport', 'expense', '公交、打车、加油等'),
    ('住房物业', '#BB8FCE', 'housing', 'expense', '房租、物业费等'),
    ('医疗保健', '#DDA0DD', 'medical', 'expense', '看病、买药等'),
    ('教育培训', '#98D8C8', 'education', 'expense', '学习、培训等'),
    ('投资理财', '#85C1E9', 'investment', 'expense', '投资、理财等'),
    ('人情社交', '#FF8C42', 'social', 'expense', '请客、送礼等'),
    ('休闲玩乐', '#87CEEB', 'entertainment', 'expense', '娱乐、旅游等'),
    ('还款', '#F8C471', 'loan', 'expense', '还款、白条等'),
    ('其他支出', '#D5DBDB', 'other', 'expense', '其他支出来源'),
]

def main():
    try:
        print("正在连接数据库...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # 查看当前分类数量
        cursor.execute("SELECT COUNT(*) as count FROM bill_categories")
        current_count = cursor.fetchone()['count']
        print(f"当前分类数量: {current_count}")
        
        # 清空表数据并重置ID序列
        print("清空表数据并重置ID序列...")
        cursor.execute("TRUNCATE TABLE bill_categories RESTART IDENTITY CASCADE")
        
        # 确保序列从1开始
        cursor.execute("ALTER SEQUENCE bill_categories_id_seq RESTART WITH 1")
        print("✅ 表数据已清空，ID序列已重置为从1开始")
        
        print(f"\n开始插入 {len(CATEGORIES)} 个分类...")
        
        # 插入分类数据
        for i, (category_name, color, icon, category_type, description) in enumerate(CATEGORIES, 1):
            cursor.execute("""
                INSERT INTO bill_categories (category_name, color, icon, category_type, description)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """, (category_name, color, icon, category_type, description))
            
            inserted_id = cursor.fetchone()['id']
            print(f"  {inserted_id:2d}. {category_name} ({category_type}) - {description}")
        
        conn.commit()
        print("\n✅ 分类数据插入完成！")
        
        # 验证结果
        cursor.execute("SELECT COUNT(*) as count FROM bill_categories")
        final_count = cursor.fetchone()['count']
        print(f"\n最终分类数量: {final_count}")
        
        # 按类型统计
        cursor.execute("""
            SELECT category_type, COUNT(*) as count 
            FROM bill_categories 
            GROUP BY category_type 
            ORDER BY category_type
        """)
        type_counts = cursor.fetchall()
        print("\n分类统计:")
        for tc in type_counts:
            print(f"  - {tc['category_type']}: {tc['count']} 个")
        
        # 显示ID范围
        cursor.execute("SELECT MIN(id) as min_id, MAX(id) as max_id FROM bill_categories")
        id_range = cursor.fetchone()
        print(f"\nID范围: {id_range['min_id']} - {id_range['max_id']}")
        
        cursor.close()
        conn.close()
        print("\n数据库连接已关闭")
        
    except Exception as e:
        print(f"错误: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    main()