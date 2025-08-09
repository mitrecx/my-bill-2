#!/usr/bin/env python3
"""
重新初始化账单分类数据
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv('backend/config/environments/development.env')

# 数据库连接配置
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"

# 预定义的分类数据
CATEGORIES = [
    # 收入分类
    ('工资收入', '#52C41A', 'salary', 'income', '工资、奖金等'),
    ('投资收益', '#1890FF', 'investment', 'income', '股票、基金、理财等'),
    ('兼职收入', '#722ED1', 'parttime', 'income', '副业、兼职等'),
    ('借款收入', '#FA8C16', 'loan', 'income', '向他人借款'),
    ('退款收入', '#13C2C2', 'refund', 'income', '各种退款'),
    ('红包收入', '#F5222D', 'redpacket', 'income', '红包、礼金等'),
    ('其他收入', '#8C8C8C', 'other', 'income', '其他收入来源'),
    
    # 支出分类
    ('食品餐饮', '#FF6B6B', 'food', 'expense', '餐饮、零食等'),
    ('服饰鞋包', '#4ECDC4', 'clothing', 'expense', '衣服、鞋子、包包等'),
    ('美妆个护', '#FF69B4', 'beauty', 'expense', '化妆品、护肤品等'),
    ('日用百货', '#45B7D1', 'daily', 'expense', '日常用品'),
    ('交通出行', '#FFEAA7', 'transport', 'expense', '公交、打车、加油等'),
    ('住房物业', '#BB8FCE', 'housing', 'expense', '房租、物业费等'),
    ('医疗保健', '#DDA0DD', 'medical', 'expense', '看病、买药等'),
    ('教育培训', '#98D8C8', 'education', 'expense', '学习、培训等'),
    ('投资理财', '#85C1E9', 'investment', 'expense', '投资、理财等'),
    ('人情社交', '#FF8C42', 'social', 'expense', '请客、送礼等'),
    ('休闲玩乐', '#87CEEB', 'entertainment', 'expense', '娱乐、旅游等'),
    ('借还款', '#F8C471', 'loan', 'expense', '还款、白条等'),
    ('其他', '#D5DBDB', 'other', 'expense', '其他支出'),
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
        
        # 查看当前分类
        cursor.execute("SELECT category_name, category_type FROM bill_categories ORDER BY category_type, category_name")
        current_categories = cursor.fetchall()
        print("\n当前分类:")
        for cat in current_categories:
            print(f"  - {cat['category_name']} ({cat['category_type']})")
        
        # 检查是否需要添加标准分类
        expected_categories = set((cat[0], cat[3]) for cat in CATEGORIES)  # (name, type)
        existing_categories = set((cat['category_name'], cat['category_type']) for cat in current_categories)
        
        missing_categories = expected_categories - existing_categories
        
        if missing_categories:
            print(f"\n发现缺失的分类 {len(missing_categories)} 个，开始添加...")
            
            for category_name, color, icon, category_type, description in CATEGORIES:
                # 检查分类是否已存在
                cursor.execute(
                    "SELECT id FROM bill_categories WHERE category_name = %s AND category_type = %s",
                    (category_name, category_type)
                )
                
                if not cursor.fetchone():
                    # 插入新分类
                    cursor.execute("""
                        INSERT INTO bill_categories (category_name, color, icon, category_type, description)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (category_name, color, icon, category_type, description))
                    print(f"  ✅ 添加分类: {category_name} ({category_type})")
                else:
                    print(f"  ⏭️  分类已存在: {category_name} ({category_type})")
            
            conn.commit()
            print("\n分类数据初始化完成！")
        else:
            print("\n所有标准分类都已存在，无需添加。")
        
        # 显示最终结果
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