#!/usr/bin/env python3
"""
测试批量分类接口的描述构建逻辑
"""

import sys
import os

# 添加backend目录到Python路径
backend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_dir)

from config.database import SessionLocal
from models.bill import Bill

def test_batch_description_logic():
    """测试批量分类接口的描述构建逻辑"""
    db = SessionLocal()
    
    try:
        # 获取日志中提到的京东账单
        bill_ids = [13451, 13452, 13453]
        bills = db.query(Bill).filter(
            Bill.id.in_(bill_ids)
        ).all()
        
        print(f"找到 {len(bills)} 个账单")
        
        # 模拟批量分类接口中的描述构建逻辑
        bills_data = []
        for bill in bills:
            print(f"\n=== 处理账单 {bill.id} ===")
            print(f"source_type: {bill.source_type}")
            print(f"transaction_desc: {bill.transaction_desc}")
            print(f"raw_data类型: {type(bill.raw_data)}")
            print(f"raw_data: {bill.raw_data}")
            
            # 构建描述：组合交易说明和交易分类
            description_parts = []
            if bill.transaction_desc:
                description_parts.append(bill.transaction_desc)
                print(f"添加transaction_desc: {bill.transaction_desc}")
            
            # 从raw_data中获取交易分类（仅对京东账单）
            print(f"检查条件: source_type == 'jd': {bill.source_type == 'jd'}")
            print(f"检查条件: raw_data存在: {bill.raw_data is not None}")
            print(f"检查条件: raw_data是字典: {isinstance(bill.raw_data, dict)}")
            
            if bill.source_type == 'jd' and bill.raw_data and isinstance(bill.raw_data, dict):
                category = bill.raw_data.get('category')
                print(f"获取到category: {category}")
                if category and category.strip():
                    description_parts.append(f"[{category}]")
                    print(f"添加category: [{category}]")
                else:
                    print("category为空或只有空白字符")
            else:
                print("不满足京东账单条件")
            
            final_description = ' '.join(description_parts) if description_parts else ''
            print(f"最终描述: {final_description}")
            
            bill_data = {
                'id': bill.id,
                'amount': bill.amount,
                'transaction_type': bill.transaction_type,
                'description': final_description,
                'source_type': bill.source_type
            }
            bills_data.append(bill_data)
            print(f"bill_data: {bill_data}")
        
        print(f"\n=== 最终bills_data ===")
        for bill_data in bills_data:
            print(f"账单{bill_data['id']}: {bill_data['description']}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_batch_description_logic()