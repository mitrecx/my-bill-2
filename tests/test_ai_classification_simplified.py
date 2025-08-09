#!/usr/bin/env python3
"""
测试简化后的AI分类功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from sqlalchemy.orm import Session
from config.database import get_db
from services.ai_classification_service import ai_classification_service
from models.bill import BillCategory

def test_ai_classification():
    """测试AI分类功能"""
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 检查AI服务是否可用
        print(f"AI服务可用性: {ai_classification_service.is_available()}")
        
        # 获取所有分类
        categories = db.query(BillCategory).all()
        print(f"可用分类数量: {len(categories)}")
        for cat in categories:
            print(f"  ID: {cat.id}, 名称: {cat.category_name}, 类型: {cat.category_type}")
        
        # 测试账单数据
        test_bills = [
            {
                'id': 12380,
                'transaction_type': 'income',
                'description': '汇入汇款-信雅达科技股份有限公司',
                'source_type': 'cmb'
            },
            {
                'id': 12378,
                'transaction_type': 'expense', 
                'description': '一网通支付-中国铁路网络有限公司',
                'source_type': 'cmb'
            },
            {
                'id': 12379,
                'transaction_type': 'income',
                'description': '基金赎回-博时基金管理有限公司',
                'source_type': 'cmb'
            }
        ]
        
        print(f"\n=== 测试批量AI分类 ===")
        print(f"测试账单数量: {len(test_bills)}")
        
        # 调用批量分类
        results = ai_classification_service.classify_bills_batch_optimized(test_bills, db, batch_size=3)
        
        print(f"\n=== 分类结果 ===")
        for bill_id, category_name in results:
            print(f"账单ID: {bill_id}, 分类: {category_name}")
            
        # 测试单个分类
        print(f"\n=== 测试单个AI分类 ===")
        for bill in test_bills:
            category = ai_classification_service.classify_single_bill(bill, db)
            print(f"账单ID: {bill['id']}, 描述: {bill['description']}, 分类: {category}")
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_ai_classification()