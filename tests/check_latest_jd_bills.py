#!/usr/bin/env python3
"""
检查最新JD账单的raw_data
"""
import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

from config.database import get_db
from models.bill import Bill

def main():
    db = next(get_db())
    
    # 查询最新的JD账单
    bills = db.query(Bill).filter(
        Bill.source_type == 'jd',
        Bill.id.in_([13594, 13595, 13596])
    ).all()
    
    print("=== 检查最新JD账单 ===")
    for bill in bills:
        print(f"\n账单ID: {bill.id}")
        print(f"描述: {bill.transaction_desc}")
        print(f"来源类型: {bill.source_type}")
        print(f"raw_data类型: {type(bill.raw_data)}")
        
        if bill.raw_data:
            if isinstance(bill.raw_data, dict):
                print(f"raw_data: {bill.raw_data}")
                category = bill.raw_data.get('category')
                print(f"category字段: {category}")
            else:
                print(f"raw_data (非字典): {bill.raw_data}")
        else:
            print("raw_data: None")
        print("-" * 50)

if __name__ == "__main__":
    main()