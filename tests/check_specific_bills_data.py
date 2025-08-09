#!/usr/bin/env python3
"""
检查特定账单的数据
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.bill import Bill
import json

# 数据库连接
DATABASE_URL = "postgresql://josie:bills_password_2024@localhost:5432/bills_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_bills():
    """检查特定账单的数据"""
    db = SessionLocal()
    try:
        # 检查账单 13328, 13329, 13330
        bill_ids = [13328, 13329, 13330]
        
        for bill_id in bill_ids:
            print(f"\n=== 账单 {bill_id} ===")
            bill = db.query(Bill).filter(Bill.id == bill_id).first()
            
            if not bill:
                print(f"账单 {bill_id} 不存在")
                continue
            
            print(f"ID: {bill.id}")
            print(f"金额: {bill.amount}")
            print(f"交易类型: {bill.transaction_type}")
            print(f"交易描述 (transaction_desc): {bill.transaction_desc}")
            print(f"来源类型: {bill.source_type}")
            print(f"交易时间: {bill.transaction_time}")
            
            # 检查原始数据
            if bill.raw_data:
                print(f"原始数据类型: {type(bill.raw_data)}")
                if isinstance(bill.raw_data, dict):
                    print("原始数据内容:")
                    for key, value in bill.raw_data.items():
                        print(f"  {key}: {value}")
                    
                    # 特别检查交易分类
                    category = bill.raw_data.get('category')
                    if category:
                        print(f"交易分类 (category): {category}")
                    else:
                        print("交易分类 (category): 未找到")
                else:
                    print(f"原始数据: {bill.raw_data}")
            else:
                print("原始数据: 无")
            
            # 模拟构建AI分类的描述字段
            description_parts = []
            if bill.transaction_desc:
                description_parts.append(bill.transaction_desc)
            
            # 从raw_data中获取交易分类（仅对京东账单）
            if bill.source_type == 'jd' and bill.raw_data and isinstance(bill.raw_data, dict):
                category = bill.raw_data.get('category')
                if category and category.strip():
                    description_parts.append(f"[{category}]")
            
            combined_description = " ".join(description_parts)
            print(f"AI分类描述字段: {combined_description}")
            
    finally:
        db.close()

if __name__ == "__main__":
    check_bills()