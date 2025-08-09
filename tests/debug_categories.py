#!/usr/bin/env python3
"""
调试分类名称匹配问题
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.database.database import get_db
from backend.models.bill import BillCategory

def main():
    """检查数据库中的分类名称"""
    db = next(get_db())
    
    try:
        # 获取所有分类
        categories = db.query(BillCategory).all()
        
        print("数据库中的所有分类:")
        for cat in categories:
            print(f"- {cat.category_name} (类型: {cat.category_type})")
        
        print("\n分类名称列表:")
        category_names = [cat.category_name for cat in categories]
        for name in category_names:
            print(f"'{name}'")
        
        # 测试字符串匹配
        test_texts = [
            "交通出行: 公交、打车、加油等",
            "日用百货: 日常用品、家具、家电等", 
            "医疗保健: 看病、买药等",
            "食品餐饮: 餐饮、零食等"
        ]
        
        print("\n测试字符串匹配:")
        for text in test_texts:
            print(f"\n测试文本: {text}")
            for cat_name in category_names:
                if cat_name in text:
                    print(f"  匹配到: {cat_name}")
        
        # 测试具体的推理内容
        reasoning_samples = [
            "打车费用-滴滴出行 - 交通出行: 公交、打车、加油等",
            "日用品采购-天猫超市 - 日用百货: 日常用品、家具、家电等",
            "挂号费-人民医院 - 医疗保健: 看病、买药等"
        ]
        
        print("\n测试推理内容匹配:")
        for reasoning in reasoning_samples:
            print(f"\n推理内容: {reasoning}")
            best_match = None
            best_position = -1
            
            for cat_name in category_names:
                pos = reasoning.rfind(cat_name)
                if pos > best_position:
                    best_position = pos
                    best_match = cat_name
            
            if best_match:
                print(f"  最佳匹配: {best_match} (位置: {best_position})")
            else:
                print("  未找到匹配")
                
    finally:
        db.close()

if __name__ == "__main__":
    main()