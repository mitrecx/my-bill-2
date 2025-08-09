#!/usr/bin/env python3
"""
测试批量分类解析修复
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'backend'))

from config.database import SessionLocal
from models import BillCategory
from services.ai_classification_service import AIClassificationService

def test_batch_parsing():
    """测试批量分类结果解析"""
    
    # 创建数据库连接
    db = SessionLocal()
    
    try:
        # 创建AI分类服务实例
        ai_service = AIClassificationService()
        
        # 模拟账单数据
        bills_batch = [
            {'id': 11418, 'description': '测试账单1'},
            {'id': 11419, 'description': '测试账单2'},
            {'id': 11420, 'description': '测试账单3'},
        ]
        
        # 测试不同格式的AI响应
        test_responses = [
            # 格式1: 带ID的完整格式
            "11418: 其他收入 (ID: 7)\n11419: 理财投资 (ID: 16)\n11420: 其他收入 (ID: 7)",
            
            # 格式2: 简单格式（没有ID）
            "11418: 其他收入\n11419: 理财投资\n11420: 其他收入",
            
            # 格式3: 带"账单ID"前缀的格式（实际日志格式）
            "账单ID: 11418: 其他支出\n账单ID: 11419: 其他支出\n账单ID: 11420: 工资收入",
            
            # 格式4: 混合格式
            "11418: 其他收入 (ID: 7)\n11419: 理财投资\n账单ID: 11420: 其他收入",
        ]
        
        print("=== 测试批量分类解析修复 ===\n")
        
        for i, response in enumerate(test_responses, 1):
            print(f"测试格式 {i}:")
            print(f"AI响应: {response}")
            
            # 解析响应
            results = ai_service._parse_batch_classification_result(response, bills_batch, db)
            
            print(f"解析结果:")
            for bill_id, category_name in results:
                print(f"  账单{bill_id}: {category_name}")
            
            # 检查是否所有账单都被正确解析
            parsed_count = sum(1 for _, category in results if category is not None)
            print(f"成功解析: {parsed_count}/{len(bills_batch)}")
            print("-" * 50)
        
        print("✅ 批量分类解析测试完成")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_batch_parsing()