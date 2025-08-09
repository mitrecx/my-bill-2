#!/usr/bin/env python3
"""
检查京东账单的raw_data格式
"""

import sys
import os
import json

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

from config.database import SessionLocal
from models.bill import Bill

def check_jd_raw_data():
    """检查京东账单的raw_data格式"""
    db = SessionLocal()
    
    try:
        # 获取最近的京东账单（包括日志中提到的账单）
        jd_bills = db.query(Bill).filter(
            Bill.source_type == 'jd',
            Bill.id.in_([13451, 13452, 13453])
        ).all()
        
        if not jd_bills:
            # 如果没有找到指定账单，获取最近的几个京东账单
            jd_bills = db.query(Bill).filter(
                Bill.source_type == 'jd'
            ).order_by(Bill.id.desc()).limit(5).all()
        
        print(f"找到 {len(jd_bills)} 个京东账单")
        
        for bill in jd_bills:
            print(f"\n账单ID: {bill.id}")
            print(f"描述: {bill.transaction_desc}")
            print(f"raw_data类型: {type(bill.raw_data)}")
            print(f"raw_data内容: {bill.raw_data}")
            
            if bill.raw_data:
                try:
                    if isinstance(bill.raw_data, str):
                        raw_data = json.loads(bill.raw_data)
                        print(f"解析后的raw_data: {raw_data}")
                        print(f"category字段: {raw_data.get('category', '无')}")
                    elif isinstance(bill.raw_data, dict):
                        print(f"raw_data已经是字典: {bill.raw_data}")
                        print(f"category字段: {bill.raw_data.get('category', '无')}")
                    else:
                        print(f"raw_data是其他类型: {type(bill.raw_data)}")
                except json.JSONDecodeError as e:
                    print(f"JSON解析失败: {e}")
            
            print("-" * 50)
    
    finally:
        db.close()

if __name__ == "__main__":
    check_jd_raw_data()