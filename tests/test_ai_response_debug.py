#!/usr/bin/env python3
"""
测试AI分类服务的响应和解析过程
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from config.database import SessionLocal
from services.ai_classification_service import ai_classification_service
from models import BillCategory
import logging

# 设置日志级别为INFO以查看详细信息
logging.basicConfig(level=logging.INFO)

def test_ai_response_debug():
    """测试AI响应和解析过程"""
    db = SessionLocal()
    
    try:
        print("=== AI分类服务响应调试测试 ===\n")
        
        # 测试数据
        test_bills = [
            {
                'id': 12345,
                'transaction_type': '支出',
                'description': '美团外卖-麦当劳',
                'source_type': 'alipay'
            },
            {
                'id': 12346,
                'transaction_type': '支出',
                'description': '滴滴出行-打车费',
                'source_type': 'cmb'
            }
        ]
        
        print("1. 测试单个账单分类...")
        for bill in test_bills:
            print(f"\n测试账单: {bill}")
            result = ai_classification_service.classify_single_bill(bill, db)
            print(f"分类结果: {result}")
        
        print("\n2. 测试批量账单分类...")
        batch_results = ai_classification_service.classify_bills_batch_optimized(test_bills, db, batch_size=2)
        print(f"批量分类结果: {batch_results}")
        
        print("\n3. 检查数据库中的分类...")
        categories = db.query(BillCategory).all()
        print("可用分类:")
        for cat in categories:
            print(f"  - {cat.category_name} (ID: {cat.id}, 类型: {cat.category_type})")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_response_debug()