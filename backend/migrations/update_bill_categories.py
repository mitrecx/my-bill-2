#!/usr/bin/env python3
"""
更新账单分类的数据库迁移脚本
将分类更新为用户指定的20个分类
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from config.settings import settings
from config.settings import settings

def update_bill_categories():
    """更新账单分类数据"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # 开始事务
        trans = conn.begin()
        
        try:
            # 先处理外键约束，将现有账单的分类ID设为NULL
            print("处理外键约束...")
            conn.execute(text("UPDATE bills SET category_id = NULL WHERE category_id IS NOT NULL"))
            
            # 清空现有分类数据
            print("清空现有分类数据...")
            conn.execute(text("DELETE FROM bill_categories"))
            
            # 插入新的分类数据
            print("插入新的分类数据...")
            
            # 收入分类（8个）
            income_categories = [
                ("工资收入", "#52C41A", "salary", "income", "工资、奖金等"),
                ("投资收益", "#1890FF", "investment", "income", "股票、基金、理财等"),
                ("兼职收入", "#722ED1", "parttime", "income", "副业、兼职等"),
                ("借款收入", "#FA8C16", "loan", "income", "向他人借款"),
                ("退款收入", "#13C2C2", "refund", "income", "各种退款"),
                ("红包收入", "#F5222D", "redpacket", "income", "红包、礼金等"),
                ("其他收入", "#8C8C8C", "other", "income", "其他收入来源"),
            ]
            
            # 支出分类（13个）
            expense_categories = [
                ("食品餐饮", "#FF6B6B", "food", "expense", "餐饮、零食等"),
                ("服饰鞋包", "#4ECDC4", "clothing", "expense", "衣服、鞋子、包包等"),
                ("美妆个护", "#FF69B4", "beauty", "expense", "化妆品、护肤品等"),
                ("日用百货", "#45B7D1", "daily", "expense", "日常用品"),
                ("交通出行", "#FFEAA7", "transport", "expense", "公交、打车、加油等"),
                ("住房物业", "#BB8FCE", "housing", "expense", "房租、物业费等"),
                ("医疗保健", "#DDA0DD", "medical", "expense", "看病、买药等"),
                ("教育培训", "#98D8C8", "education", "expense", "学习、培训等"),
                ("投资理财", "#85C1E9", "investment", "expense", "投资、理财等"),
                ("人情社交", "#FF8C42", "social", "expense", "请客、送礼等"),
                ("休闲玩乐", "#87CEEB", "entertainment", "expense", "娱乐、旅游等"),
                ("借还款", "#F8C471", "loan", "expense", "还款、白条等"),
                ("其他", "#D5DBDB", "other", "expense", "其他支出"),
            ]
            
            # 插入收入分类
            for name, color, icon, category_type, description in income_categories:
                conn.execute(text("""
                    INSERT INTO bill_categories (category_name, color, icon, category_type, description)
                    VALUES (:name, :color, :icon, :category_type, :description)
                """), {
                    "name": name,
                    "color": color,
                    "icon": icon,
                    "category_type": category_type,
                    "description": description
                })
                print(f"插入收入分类: {name}")
            
            # 插入支出分类
            for name, color, icon, category_type, description in expense_categories:
                conn.execute(text("""
                    INSERT INTO bill_categories (category_name, color, icon, category_type, description)
                    VALUES (:name, :color, :icon, :category_type, :description)
                """), {
                    "name": name,
                    "color": color,
                    "icon": icon,
                    "category_type": category_type,
                    "description": description
                })
                print(f"插入支出分类: {name}")
            
            # 提交事务
            trans.commit()
            print("分类数据更新完成！")
            
            # 验证更新结果
            result = conn.execute(text("SELECT COUNT(*) as count FROM bill_categories"))
            count = result.fetchone()[0]
            print(f"总共插入了 {count} 个分类")
            
            # 显示分类列表
            result = conn.execute(text("""
                SELECT category_type, category_name, description 
                FROM bill_categories 
                ORDER BY category_type, id
            """))
            
            print("\n分类列表:")
            current_type = None
            for row in result:
                if row[0] != current_type:
                    current_type = row[0]
                    print(f"\n{current_type.upper()}分类:")
                print(f"  - {row[1]}: {row[2]}")
            
        except Exception as e:
            # 回滚事务
            trans.rollback()
            print(f"更新失败: {e}")
            raise

if __name__ == "__main__":
    print("开始更新账单分类...")
    update_bill_categories()
    print("更新完成！") 