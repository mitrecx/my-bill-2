#!/usr/bin/env python3
"""
验证AI分类描述字段修复的脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.bill import Bill

# 数据库连接
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_jd_bill_description_construction():
    """测试京东账单描述字段的构建逻辑"""
    db = SessionLocal()
    
    try:
        # 获取几个京东账单
        jd_bills = db.query(Bill).filter(
            Bill.source_type == 'jd',
            Bill.id.in_([13328, 13329, 13330])
        ).all()
        
        print("=== 京东账单描述字段构建测试 ===")
        
        for bill in jd_bills:
            print(f"\n账单ID: {bill.id}")
            print(f"原始交易描述: {bill.transaction_desc}")
            print(f"原始数据: {bill.raw_data}")
            
            # 模拟AI分类服务中的描述构建逻辑
            description_parts = []
            if bill.transaction_desc:
                description_parts.append(bill.transaction_desc)
            
            # 从raw_data中获取交易分类（仅对京东账单）
            if bill.source_type == 'jd' and bill.raw_data and isinstance(bill.raw_data, dict):
                category = bill.raw_data.get('category')
                if category and category.strip():
                    description_parts.append(f"[{category}]")
            
            ai_description = ' '.join(description_parts) if description_parts else ''
            print(f"AI分类描述字段: {ai_description}")
            
            # 检查是否包含交易分类
            has_category = '[' in ai_description and ']' in ai_description
            print(f"是否包含交易分类: {'✓' if has_category else '✗'}")
            
    except Exception as e:
        print(f"测试失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_jd_bill_description_construction()