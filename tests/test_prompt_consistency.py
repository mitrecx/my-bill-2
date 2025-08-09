#!/usr/bin/env python3
"""
测试单个分类和批量分类方法的提示词一致性
验证两种方法使用相同的分类逻辑和格式
"""

import sys
import os

# 添加项目根目录和backend目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, 'backend')
sys.path.insert(0, project_root)
sys.path.insert(0, backend_path)

from services.ai_classification_service import AIClassificationService
from config.database import get_db
from models.bill import BillCategory

def test_prompt_consistency():
    """测试单个分类和批量分类方法的一致性"""
    print("=== 测试提示词一致性 ===")
    
    # 获取数据库连接
    db = next(get_db())
    
    # 创建AI分类服务实例
    ai_service = AIClassificationService()
    
    # 检查AI服务是否可用
    if not ai_service.is_available():
        print("❌ AI分类服务不可用，跳过测试")
        return
    
    print("✅ AI分类服务可用")
    
    # 测试账单
    test_bill = {
        'id': 99999,
        'transaction_type': '支出',
        'description': '超市购物-沃尔玛',
        'source_type': 'cmb'
    }
    
    print(f"\n=== 测试账单信息 ===")
    print(f"账单ID: {test_bill['id']}")
    print(f"交易类型: {test_bill['transaction_type']}")
    print(f"描述: {test_bill['description']}")
    print(f"来源: {test_bill['source_type']}")
    
    print(f"\n=== 单个分类方法测试 ===")
    try:
        single_result = ai_service.classify_single_bill(test_bill, db)
        print(f"✅ 单个分类结果: {single_result}")
    except Exception as e:
        print(f"❌ 单个分类异常: {e}")
        single_result = None
    
    print(f"\n=== 批量分类方法测试 ===")
    try:
        batch_results = ai_service.classify_bills_batch_optimized([test_bill], db)
        batch_result = batch_results[0][1] if batch_results and len(batch_results) > 0 else None
        print(f"✅ 批量分类结果: {batch_result}")
    except Exception as e:
        print(f"❌ 批量分类异常: {e}")
        batch_result = None
    
    print(f"\n=== 一致性验证 ===")
    if single_result and batch_result:
        if single_result == batch_result:
            print(f"✅ 分类结果一致: {single_result}")
        else:
            print(f"⚠️  分类结果不一致:")
            print(f"   单个分类: {single_result}")
            print(f"   批量分类: {batch_result}")
    elif single_result or batch_result:
        print(f"⚠️  部分方法失败:")
        print(f"   单个分类: {single_result}")
        print(f"   批量分类: {batch_result}")
    else:
        print(f"❌ 两种方法都失败了")
    
    # 测试多个账单的批量分类
    print(f"\n=== 多账单批量分类测试 ===")
    test_bills = [
        {
            'id': 99991,
            'transaction_type': '支出',
            'description': '咖啡-星巴克',
            'source_type': 'cmb'
        },
        {
            'id': 99992,
            'transaction_type': '收入',
            'description': '奖金发放',
            'source_type': 'cmb'
        },
        {
            'id': 99993,
            'transaction_type': '支出',
            'description': '地铁卡充值',
            'source_type': 'cmb'
        }
    ]
    
    try:
        batch_results = ai_service.classify_bills_batch_optimized(test_bills, db)
        print(f"✅ 批量分类成功，处理了 {len(batch_results)} 个账单:")
        for bill_id, category in batch_results:
            print(f"   账单{bill_id}: {category}")
    except Exception as e:
        print(f"❌ 批量分类异常: {e}")
    
    print(f"\n=== 测试完成 ===")
    
    # 关闭数据库连接
    db.close()

if __name__ == "__main__":
    test_prompt_consistency()