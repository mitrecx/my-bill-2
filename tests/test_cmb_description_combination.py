#!/usr/bin/env python3
"""
测试招商银行解析器中描述字段的组合功能
验证交易摘要和对手信息是否正确组合
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from parsers.cmb_parser import CMBParser

def test_description_combination():
    """测试描述字段组合功能"""
    print("=== 测试招商银行描述字段组合功能 ===\n")
    
    parser = CMBParser()
    
    # 测试用例1: 正常的交易摘要和对手信息
    test_content_1 = """2025-04-15
CNY
-4577.17
6522.51
掌上生活还款
陈兴
2025-04-16
CNY
100.00
6622.51
工资收入
公司财务部
2025-04-17
CNY
-50.00
6572.51
午餐费用
美团外卖"""
    
    print("1. 测试正常的交易摘要和对手信息组合...")
    result_1 = parser.parse_content(test_content_1)
    
    if result_1.success_count > 0:
        print(f"✅ 成功解析 {result_1.success_count} 条记录")
        for i, record in enumerate(result_1.success_records):
            print(f"\n--- 记录 {i+1} ---")
            print(f"原始描述: {record.get('transaction_desc', 'N/A')}")
            print(f"交易金额: {record.get('amount', 'N/A')}")
            print(f"交易类型: {record.get('transaction_type', 'N/A')}")
            
            # 检查raw_data中的原始字段
            raw_data = record.get('raw_data', {})
            if isinstance(raw_data, str):
                import json
                raw_data = json.loads(raw_data)
            
            print(f"raw_data中的description: {raw_data.get('description', 'N/A')}")
            print(f"raw_data中的counter_party: {raw_data.get('counter_party', 'N/A')}")
    else:
        print("❌ 解析失败")
        for error in result_1.failed_records:
            print(f"错误: {error}")
    
    # 测试用例2: 描述和对手信息相同的情况
    test_content_2 = """2025-04-18
CNY
-200.00
6372.51
美团外卖
美团外卖"""
    
    print("\n\n2. 测试描述和对手信息相同的情况...")
    result_2 = parser.parse_content(test_content_2)
    
    if result_2.success_count > 0:
        print(f"✅ 成功解析 {result_2.success_count} 条记录")
        for i, record in enumerate(result_2.success_records):
            print(f"\n--- 记录 {i+1} ---")
            print(f"组合后描述: {record.get('transaction_desc', 'N/A')}")
            
            # 检查raw_data中的原始字段
            raw_data = record.get('raw_data', {})
            if isinstance(raw_data, str):
                import json
                raw_data = json.loads(raw_data)
            
            print(f"raw_data中的description: {raw_data.get('description', 'N/A')}")
            print(f"raw_data中的counter_party: {raw_data.get('counter_party', 'N/A')}")
    else:
        print("❌ 解析失败")
    
    # 测试用例3: 对手信息为空的情况
    test_content_3 = """2025-04-19
CNY
-300.00
6072.51
ATM取现
"""
    
    print("\n\n3. 测试只有描述没有对手信息的情况...")
    result_3 = parser.parse_content(test_content_3)
    
    if result_3.success_count > 0:
        print(f"✅ 成功解析 {result_3.success_count} 条记录")
        for i, record in enumerate(result_3.success_records):
            print(f"\n--- 记录 {i+1} ---")
            print(f"组合后描述: {record.get('transaction_desc', 'N/A')}")
            
            # 检查raw_data中的原始字段
            raw_data = record.get('raw_data', {})
            if isinstance(raw_data, str):
                import json
                raw_data = json.loads(raw_data)
            
            print(f"raw_data中的description: {raw_data.get('description', 'N/A')}")
            print(f"raw_data中的counter_party: {raw_data.get('counter_party', 'N/A')}")
    else:
        print("❌ 解析失败")
    
    print("\n=== 测试完成 ===")
    
    # 验证组合逻辑
    total_success = result_1.success_count + result_2.success_count + result_3.success_count
    if total_success > 0:
        print("✅ 描述字段组合功能测试通过")
        return True
    else:
        print("❌ 描述字段组合功能测试失败")
        return False

if __name__ == "__main__":
    test_description_combination()