#!/usr/bin/env python3
"""
测试更新后的classify_single_bill方法
验证提示词一致性和简化的响应解析逻辑
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

def test_classify_single_bill():
    """测试单个账单分类功能"""
    print("=== 测试更新后的classify_single_bill方法 ===")
    
    # 获取数据库连接
    db = next(get_db())
    
    # 创建AI分类服务实例
    ai_service = AIClassificationService()
    
    # 检查AI服务是否可用
    if not ai_service.is_available():
        print("❌ AI分类服务不可用，跳过测试")
        return
    
    print("✅ AI分类服务可用")
    
    # 获取可用分类
    categories = db.query(BillCategory).all()
    print(f"✅ 数据库中有 {len(categories)} 个分类")
    
    # 测试用例
    test_bills = [
        {
            'id': 12345,
            'transaction_type': '支出',
            'description': '午餐-麦当劳',
            'source_type': 'cmb'
        },
        {
            'id': 12346,
            'transaction_type': '支出',
            'description': '打车费用-滴滴出行',
            'source_type': 'cmb'
        },
        {
            'id': 12347,
            'transaction_type': '收入',
            'description': '工资发放',
            'source_type': 'cmb'
        },
        {
            'id': 12348,
            'transaction_type': '支出',
            'description': '挂号费-人民医院',
            'source_type': 'cmb'
        }
    ]
    
    print("\n=== 开始测试账单分类 ===")
    
    for i, bill in enumerate(test_bills, 1):
        print(f"\n--- 测试账单 {i} ---")
        print(f"账单ID: {bill['id']}")
        print(f"交易类型: {bill['transaction_type']}")
        print(f"描述: {bill['description']}")
        print(f"来源: {bill['source_type']}")
        
        try:
            # 调用分类方法
            result = ai_service.classify_single_bill(bill, db)
            
            if result:
                print(f"✅ 分类结果: {result}")
                
                # 验证分类是否存在于数据库中
                category = db.query(BillCategory).filter(
                    BillCategory.category_name == result
                ).first()
                
                if category:
                    print(f"✅ 分类验证通过: {result} (ID: {category.id})")
                else:
                    print(f"❌ 分类验证失败: {result} 不存在于数据库中")
            else:
                print("❌ 分类失败: 返回None")
                
        except Exception as e:
            print(f"❌ 分类异常: {e}")
    
    print("\n=== 测试完成 ===")
    
    # 关闭数据库连接
    db.close()

if __name__ == "__main__":
    test_classify_single_bill()